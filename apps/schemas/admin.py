from django import forms
from django.contrib import admin, messages
from django.contrib.contenttypes.admin import GenericTabularInline
from django.core.exceptions import ValidationError
from django.db import models
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.text import slugify

from schemas.config import SCHEMA_CONFIG_REGISTRY
from schemas.models import (
    Schema,
    SchemaColumn,
    SchemaColumnValue,
    SchemaColumnVisibility,
    CustomAssetSchemaConfig,
)
from schemas.services.holding_sync_service import sync_schema_column_to_holdings, apply_base_scv_to_holding
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

# ----------------------
# Helpers / Widgets (for built-ins on Schema admin)
# ----------------------


class DisabledOptionSelect(forms.Select):
    def __init__(self, *args, disabled_values=None, **kwargs):
        self.disabled_values = set(disabled_values or [])
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected,
                                       index, subindex=subindex, attrs=attrs)
        if value in self.disabled_values:
            option['attrs']['disabled'] = True
        return option


def build_builtin_choices_for_schema(schema):
    if not schema:
        return [], set(), None
    config = (SCHEMA_CONFIG_REGISTRY.get(schema.schema_type)
              or SCHEMA_CONFIG_REGISTRY.get(f"{schema.schema_type}_self_managed"))
    if not config:
        return [], set(), None

    existing = {
        f"{c.source}:{c.source_field}"
        for c in schema.columns.exclude(source__isnull=True).exclude(source_field__isnull=True)
    }

    choices, disabled = [], set()
    for group_label, fields in config.items():
        group = []
        for source_field, spec in fields.items():
            key = f"{group_label}:{source_field}"
            label = spec.get("title", source_field.replace("_", " ").title())
            group.append((key, label))
            if key in existing:
                disabled.add(key)
        if group:
            choices.append((group_label.title(), group))
    return choices, disabled, config


# ----------------------
# Schema admin: add built-ins (button + inline)
# ----------------------
class AddBuiltInColumnForm(forms.Form):
    catalog_item = forms.ChoiceField(label="Built-in column")

    def __init__(self, *args, schema: Schema, **kwargs):
        super().__init__(*args, **kwargs)
        self.schema = schema
        choices, disabled, _ = build_builtin_choices_for_schema(schema)
        self.fields['catalog_item'].widget = DisabledOptionSelect(
            disabled_values=disabled)
        self.fields['catalog_item'].choices = choices

    def create_column(self):
        key = self.cleaned_data['catalog_item']
        source, source_field = key.split(":", 1)
        _, _, config = build_builtin_choices_for_schema(self.schema)
        spec = config[source][source_field]

        obj, created = SchemaColumn.objects.get_or_create(
            schema=self.schema,
            source=source,
            source_field=source_field,
            defaults={
                "title": spec["title"],
                "data_type": spec["data_type"],
                "field_path": spec.get("field_path"),
                "decimal_places": spec.get("decimal_places"),
                "editable": spec.get("editable", False),
                "is_deletable": spec.get("is_deletable", False),
                "is_system": spec.get("is_system", True),
                "display_order": (self.schema.columns.aggregate(models.Max("display_order"))["display_order__max"] or 0) + 1,
                "formula_method": spec.get("formula_method"),
                "formula_expression": spec.get("formula"),
            }
        )
        return obj, created


class SchemaColumnInlineForm(forms.ModelForm):
    built_in = forms.ChoiceField(label="Built-in column", required=False)

    class Meta:
        model = SchemaColumn
        fields = (
            "custom_title",                 # only editable for system rows
            "title", "data_type", "decimal_places",
            "source", "source_field", "field_path",
            "editable", "is_deletable",
            "is_system", "scope",
            "display_order", "investment_theme",
        )

    _builtin_choices = []
    _builtin_disabled = set()
    _config = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['built_in'].widget = DisabledOptionSelect(
            disabled_values=getattr(self, "_builtin_disabled", set())
        )
        self.fields['built_in'].choices = getattr(self, "_builtin_choices", [])

        inst = self.instance
        if inst and inst.pk:
            if inst.is_system:
                # system: lock structure; allow custom_title only
                keep = {"custom_title"}
                for name, field in self.fields.items():
                    if name not in keep:
                        field.disabled = True
            self.fields['built_in'].widget = forms.HiddenInput()
        else:
            # new row: pick built-in; structure will be filled in clean()
            for name in ("title", "data_type", "decimal_places", "source", "source_field", "field_path",
                         "editable", "is_deletable", "is_system"):
                if name in self.fields:
                    self.fields[name].disabled = True

    def clean(self):
        cleaned = super().clean()
        bi = cleaned.get("built_in")
        is_new = not self.instance.pk

        if is_new and bi:
            if bi in getattr(self, "_builtin_disabled", set()):
                raise forms.ValidationError(
                    "This built-in column already exists in this schema.")
            source, source_field = bi.split(":", 1)
            spec = self._config[source][source_field]
            cleaned.update({
                "source": source,
                "source_field": source_field,
                "title": spec["title"],
                "data_type": spec["data_type"],
                "field_path": spec.get("field_path"),
                "decimal_places": spec.get("decimal_places"),
                "editable": spec.get("editable", False),
                "is_deletable": spec.get("is_deletable", False),
                "is_system": spec.get("is_system", True),
            })
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not self.instance.pk and (obj.display_order in (None, 0)):
            max_order = SchemaColumn.objects.filter(schema=obj.schema).aggregate(
                models.Max("display_order"))["display_order__max"] or 0
            obj.display_order = max_order + 1
        if commit:
            obj.save()
        return obj


class SchemaColumnInline(admin.TabularInline):
    model = SchemaColumn
    form = SchemaColumnInlineForm
    extra = 0
    fields = (
        "built_in",  # grouped built-ins
        "custom_title",
        "title", "data_type", "decimal_places",
        "source", "source_field", "field_path",
        "editable", "is_deletable",
        "is_system", "scope",
        "display_order", "investment_theme",
    )
    ordering = ("display_order",)
    show_change_link = True

    def get_formset(self, request, obj=None, **kwargs):
        FormClass = self.form
        choices, disabled, config = build_builtin_choices_for_schema(obj)

        class DynamicForm(FormClass):
            _builtin_choices = choices
            _builtin_disabled = disabled
            _config = config

        kwargs["form"] = DynamicForm
        return super().get_formset(request, obj, **kwargs)


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "schema_type",
                    "content_type", "object_id", "created_at")
    search_fields = ("name", "schema_type")
    list_filter = ("schema_type", "content_type")
    readonly_fields = ("created_at",)
    inlines = [SchemaColumnInline]
    change_form_template = "admin/schemas/schema/change_form.html"

    def save_formset(self, request, form, formset, change):
        instances = formset.save()
        if formset.model is SchemaColumn:
            for obj in getattr(formset, "new_objects", []):
                sync_schema_column_to_holdings(obj)
        return instances

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<int:object_id>/add_builtin/",
                self.admin_site.admin_view(self.add_builtin_view),
                name="schemas_schema_add_builtin",
            )
        ]
        return custom + urls

    def add_builtin_view(self, request, object_id):
        schema = self.get_object(request, object_id)
        if not schema:
            self.message_user(request, "Schema not found.",
                              level=messages.ERROR)
            return redirect("admin:schemas_schema_changelist")

        if request.method == "POST":
            form = AddBuiltInColumnForm(request.POST, schema=schema)
            if form.is_valid():
                col, created = form.create_column()
                if created:
                    sync_schema_column_to_holdings(col)
                    self.message_user(
                        request, f"Added built-in column “{col.title}”.")
                else:
                    self.message_user(
                        request, "That column already exists.", level=messages.WARNING)
                return redirect(reverse("admin:schemas_schema_change", args=[schema.pk]))
        else:
            form = AddBuiltInColumnForm(schema=schema)

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "original": schema,
            "title": "Add built-in column",
            "form": form,
            "media": self.media + form.media,
            "has_view_permission": True,
            "has_change_permission": True,
            "add_builtin_url": request.path,
            "return_url": reverse("admin:schemas_schema_change", args=[schema.pk]),
        }
        return TemplateResponse(request, "admin/schemas/schema/add_builtin.html", context)


# ----------------------
# SchemaColumn admin: custom-only (simple)
# ----------------------
class SchemaColumnCustomAddForm(forms.ModelForm):
    class Meta:
        model = SchemaColumn
        fields = (
            "schema",
            "title",
            "data_type",
            "decimal_places",
            "editable",
            "scope",
            "display_order",
            "investment_theme",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["data_type"].choices = [
            ("string", "String"), ("decimal", "Decimal")]
        # <- fixed
        self.fields["decimal_places"].initial = self.fields["decimal_places"].initial or 2

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("data_type") == "decimal":
            dp = cleaned.get("decimal_places")
            if dp is None:
                self.add_error("decimal_places",
                               "Required for decimal columns.")
            elif not (0 <= int(dp) <= 8):
                self.add_error("decimal_places", "Must be between 0 and 8.")
        else:
            cleaned["decimal_places"] = None
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        # Always custom + deletable
        obj.source = "custom"
        obj.is_system = False
        obj.is_deletable = True
        obj.field_path = None
        obj.formula_method = None
        obj.formula_expression = None

        # Generate unique-ish source_field within schema
        if not obj.source_field:
            base = slugify(self.cleaned_data.get(
                "title") or "") or "custom_field"
            sf = base
            i = 1
            while SchemaColumn.objects.filter(schema=obj.schema, source="custom", source_field=sf).exists():
                i += 1
                sf = f"{base}_{i}"
            obj.source_field = sf

        if commit:
            obj.save()
        return obj


@admin.register(SchemaColumn)
class SchemaColumnAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'schema', 'title', 'custom_title', 'source', 'source_field',
        'data_type', 'decimal_places', 'editable', 'is_deletable',
        'is_system', 'scope', 'display_order', 'investment_theme',
    )
    list_filter = ('schema', 'source', 'data_type', 'editable',
                   'is_deletable', 'is_system', 'scope')
    search_fields = ('title', 'custom_title', 'source_field')
    raw_id_fields = ('schema', 'investment_theme',)

    def get_fieldsets(self, request, obj=None):
        # Custom rows: minimal fields
        if obj is None or (obj and obj.source == "custom"):
            return ((None, {
                "fields": (
                    "schema",
                    "title",
                    ("data_type", "decimal_places"),
                    "editable",
                    ("scope", "display_order"),
                    "investment_theme",
                )
            }),)
        # System rows: show full structure (readonly via get_readonly_fields)
        return ((None, {
            "fields": (
                "schema",
                ("title", "custom_title"),
                ("data_type", "decimal_places"),
                ("source", "source_field", "field_path"),
                ("formula_method", "formula_expression"),
                ("editable", "is_deletable"),
                ("is_system", "scope", "display_order"),
                "investment_theme",
            )
        }),)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs["form"] = SchemaColumnCustomAddForm
        return super().get_form(request, obj, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if obj and obj.source == "custom":
            # Always deletable; hide system-ish fields for custom rows
            ro += ['is_deletable', 'is_system', 'source', 'source_field',
                   'field_path', 'formula_method', 'formula_expression', 'custom_title']
        elif obj and obj.is_system:
            ro += ['data_type', 'decimal_places', 'source',
                   'source_field', 'field_path', 'is_system']
        return ro

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        if is_new:
            obj.source = "custom"
            obj.is_system = False
            obj.is_deletable = True
            obj.field_path = None
            if not obj.source_field:
                obj.source_field = slugify(obj.title or "") or "custom_field"
        super().save_model(request, obj, form, change)
        if is_new:
            sync_schema_column_to_holdings(obj)


# ----------------------
# SCV / Visibility / Asset config admins
# ----------------------
class SchemaColumnValueInline(GenericTabularInline):
    model = SchemaColumnValue
    extra = 0
    fields = ("column", "value", "is_edited")
    readonly_fields = ("is_edited",)
    autocomplete_fields = ("column",)


class SchemaColumnValueAdminForm(forms.ModelForm):
    class Meta:
        model = SchemaColumnValue
        fields = "__all__"

    def _to_decimal(self, raw):
        """
        Robustly convert admin input (Decimal/str/float/int) to Decimal.
        Accepts thousand separators and trims whitespace. Empty -> None.
        """
        if raw is None:
            return None
        if isinstance(raw, Decimal):
            return raw
        if isinstance(raw, (int, float)):
            return Decimal(str(raw))
        if isinstance(raw, str):
            s = raw.strip()
            if s == "":
                return None
            # drop thousand separators, keep minus and dot
            s = s.replace(",", "")
            return Decimal(s)
        # unknown type → invalid
        raise InvalidOperation("Unsupported type")

    def clean(self):
        cleaned = super().clean()

        obj = self.instance  # existing SCV row we’re editing
        col = obj.column
        val = cleaned.get("value")

        if not col:
            return cleaned  # nothing to do

        # 1) Normalize decimals (friendly UX: round instead of rejecting)
        if col.data_type == "decimal" and val is not None:
            try:
                dec = self._to_decimal(val)
                if dec is not None:
                    places = col.decimal_places or 4
                    quant = Decimal(1).scaleb(-places)  # 10**(-places)
                    dec = dec.quantize(quant, rounding=ROUND_HALF_UP)
                cleaned["value"] = dec
                val = dec  # use rounded value for downstream validation
            except (InvalidOperation, ValueError):
                self.add_error("value", "Invalid decimal format.")
                return cleaned

        # 2) If base (holding) field → validate on the Holding itself
        if col.source == "holding":
            model = obj.account_ct.model_class()
            holding = model.objects.filter(pk=obj.account_id).first()
            if holding:
                try:
                    # Coerce for model assignment
                    coerced = val if col.data_type != "decimal" else (
                        None if val is None else Decimal(str(val)))
                    setattr(holding, col.source_field, coerced)
                    holding.full_clean()  # e.g. “Quantity cannot be negative.”
                except ValidationError as ve:
                    # Show the model’s error on the SCV value field (no 500)
                    self.add_error("value", "; ".join(ve.messages))

        return cleaned


@admin.register(SchemaColumnValue)
class SchemaColumnValueAdmin(admin.ModelAdmin):
    form = SchemaColumnValueAdminForm  # ← use our validating form
    list_display = ("id", "column", "account", "value", "is_edited")
    list_filter = ("column__schema", "is_edited")
    search_fields = ("column__title",)
    autocomplete_fields = ("column",)
    actions = ("reset_overrides",)

    def save_model(self, request, obj, form, change):
        """
        After form validation passed:
        - For holding source: save SCV, mark not edited, push into holding,
          let holding.save() re-sync base+calculated.
        - For other sources: default behavior.
        """
        col = obj.column

        if col and col.source == "holding":
            super().save_model(request, obj, form, change)

            # Model is the source of truth → ensure SCV isn’t left “edited”
            if obj.is_edited:
                obj.is_edited = False
                obj.save(update_fields=["is_edited"])

            # Apply SCV value into holding (holding.save() will sync & calc)
            try:
                apply_base_scv_to_holding(obj)
                messages.success(
                    request, f"Updated {col.title} on holding and recalculated.")
            except ValidationError as ve:
                # Shouldn’t happen because form clean already validated, but be safe
                messages.error(request, "; ".join(ve.messages))
            return

        # Not a holding-sourced SCV → default save
        super().save_model(request, obj, form, change)

    def reset_overrides(self, request, queryset):
        updated = queryset.update(is_edited=False, value=None)
        self.message_user(request, f"Reset {updated} override(s).")
    reset_overrides.short_description = "Reset edited values to defaults"


@admin.register(SchemaColumnVisibility)
class SchemaColumnVisibilityAdmin(admin.ModelAdmin):
    list_display = ("id", "column", "account", "is_visible")
    list_filter = ("is_visible", "column__schema")
    search_fields = ("column__title",)
    autocomplete_fields = ("column",)


@admin.register(CustomAssetSchemaConfig)
class AssetSchemaConfigAdmin(admin.ModelAdmin):
    list_display = ['asset_type', 'created_at', 'updated_at']
    search_fields = ['asset_type']
