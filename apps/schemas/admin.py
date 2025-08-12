from django import forms
from django.contrib import admin, messages
from django.contrib.contenttypes.admin import GenericTabularInline
from django.db import models
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse

from schemas.config import SCHEMA_CONFIG_REGISTRY
from schemas.models import (
    Schema,
    SchemaColumn,
    SchemaColumnValue,
    SchemaColumnVisibility,
    CustomAssetSchemaConfig,
)
from schemas.services.holding_sync_service import sync_schema_column_to_holdings


# ----------------------
# Helpers / Widgets
# ----------------------
class DisabledOptionSelect(forms.Select):
    """Select that allows disabling some options (used for built-in catalog)."""

    def __init__(self, *args, disabled_values=None, **kwargs):
        self.disabled_values = set(disabled_values or [])
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        if value in self.disabled_values:
            option['attrs']['disabled'] = True
        return option


def build_builtin_choices_for_schema(schema):
    """
    Returns (choices, disabled_set, config) for a given Schema.
    choices -> [("Asset", [(key,label), ...]), ("Holding", ...), ("Calculated", ...)]
    disabled_set -> keys already present in this schema ("source:source_field")
    """
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
# Schema Admin: Add built-ins (button)
# ----------------------
class AddBuiltInColumnForm(forms.Form):
    catalog_item = forms.ChoiceField(label="Built-in column")

    def __init__(self, *args, schema: Schema, **kwargs):
        super().__init__(*args, **kwargs)
        self.schema = schema
        choices, disabled, _ = build_builtin_choices_for_schema(schema)
        self.fields['catalog_item'].widget = DisabledOptionSelect(disabled_values=disabled)
        self.fields['catalog_item'].choices = choices

    def create_column(self):
        """Create the selected SchemaColumn from config."""
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
                "editable": spec.get("editable", False),     # value editability
                "is_deletable": spec.get("is_deletable", False),
                "is_system": spec.get("is_system", True),
                "display_order": (self.schema.columns.aggregate(models.Max("display_order"))["display_order__max"] or 0) + 1,
                "formula_method": spec.get("formula_method"),
                "formula_expression": spec.get("formula"),
            }
        )
        return obj, created


# ----------------------
# Schema Inline (Columns): built-in dropdown on NEW rows, lock system rows
# ----------------------
class SchemaColumnInlineForm(forms.ModelForm):
    built_in = forms.ChoiceField(label="Built-in column", required=False)

    class Meta:
        model = SchemaColumn
        # Note: 'built_in' is extra and not listed here
        fields = (
            "custom_title",
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

        # Wire choices + disabled for the dropdown
        self.fields['built_in'].widget = DisabledOptionSelect(
            disabled_values=getattr(self, "_builtin_disabled", set())
        )
        self.fields['built_in'].choices = getattr(self, "_builtin_choices", [])

        inst = self.instance

        if inst and inst.pk:
            # Existing row
            if inst.is_system:
                # lock structure; only custom_title editable
                keep = {"custom_title"}
                for name, field in self.fields.items():
                    if name not in keep:
                        field.disabled = True
                self.fields['built_in'].widget = forms.HiddenInput()
            else:
                self.fields['built_in'].widget = forms.HiddenInput()
        else:
            # New row: encourage picking built-in; disable structure inputs for now
            for name in ("title", "data_type", "decimal_places", "source", "source_field", "field_path",
                         "editable", "is_deletable", "is_system"):
                if name in self.fields:
                    self.fields[name].disabled = True  # filled from config in clean()

    def clean(self):
        cleaned = super().clean()
        bi = cleaned.get("built_in")
        is_new = not self.instance.pk

        if is_new and bi:
            if bi in getattr(self, "_builtin_disabled", set()):
                raise forms.ValidationError("This built-in column already exists in this schema.")

            source, source_field = bi.split(":", 1)
            spec = self._config[source][source_field]

            # Fill from config (mark as system)
            cleaned["source"] = source
            cleaned["source_field"] = source_field
            cleaned["title"] = spec["title"]
            cleaned["data_type"] = spec["data_type"]
            cleaned["field_path"] = spec.get("field_path")
            cleaned["decimal_places"] = spec.get("decimal_places")
            cleaned["editable"] = spec.get("editable", False)
            cleaned["is_deletable"] = spec.get("is_deletable", False)
            cleaned["is_system"] = spec.get("is_system", True)
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not self.instance.pk:
            if obj.display_order in (None, 0):
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
        "built_in",  # show catalog selector on new rows
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
        # obj is the parent Schema
        FormClass = self.form
        choices, disabled, config = build_builtin_choices_for_schema(obj)

        class DynamicForm(FormClass):
            _builtin_choices = choices
            _builtin_disabled = disabled
            _config = config

        kwargs["form"] = DynamicForm
        return super().get_formset(request, obj, **kwargs)


# ----------------------
# Schema Admin (button to add built-ins)
# ----------------------
@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "schema_type", "content_type", "object_id", "created_at")
    search_fields = ("name", "schema_type")
    list_filter = ("schema_type", "content_type")
    readonly_fields = ("created_at",)
    inlines = [SchemaColumnInline]
    change_form_template = "admin/schemas/schema/change_form.html"  # shows "Add built-in column" button

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
            self.message_user(request, "Schema not found.", level=messages.ERROR)
            return redirect("admin:schemas_schema_changelist")

        if request.method == "POST":
            form = AddBuiltInColumnForm(request.POST, schema=schema)
            if form.is_valid():
                col, created = form.create_column()
                if created:
                    sync_schema_column_to_holdings(col)
                    self.message_user(request, f"Added built-in column “{col.title}”.")
                else:
                    self.message_user(request, "That column already exists.", level=messages.WARNING)
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
# SchemaColumn Admin (custom-only on Add; system rows locked on Change)
# ----------------------
class SchemaColumnCustomAddForm(forms.ModelForm):
    class Meta:
        model = SchemaColumn
        # fields for custom creation
        fields = (
            "schema",
            "title", "custom_title",
            "data_type", "decimal_places",
            "editable", "is_deletable",
            "scope", "display_order",
            "investment_theme",
        )

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.source = "custom"
        obj.is_system = False
        if not obj.source_field:
            # derive a reasonable source_field from the title
            from django.utils.text import slugify
            obj.source_field = slugify(self.cleaned_data.get("title") or "") or None
        obj.field_path = None
        obj.formula_method = None
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
    list_filter = ('schema', 'source', 'data_type', 'editable', 'is_deletable', 'is_system', 'scope')
    search_fields = ('title', 'custom_title', 'source_field')
    raw_id_fields = ('schema', 'investment_theme',)

    fieldsets = (
        (None, {
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
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        # On Add, force custom-creation form (no built-in button here)
        if obj is None:
            kwargs["form"] = SchemaColumnCustomAddForm
        return super().get_form(request, obj, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if obj and obj.is_system:
            ro += ['data_type', 'decimal_places', 'source', 'source_field', 'field_path']
        return ro

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        if is_new:
            # double-enforce custom on Add
            obj.source = "custom"
            obj.is_system = False
            if not obj.source_field:
                from django.utils.text import slugify
                obj.source_field = slugify(obj.title or "") or None
            obj.field_path = None
        super().save_model(request, obj, form, change)
        if is_new:
            sync_schema_column_to_holdings(obj)


# ----------------------
# SchemaColumnValue / Visibility / CustomAssetSchemaConfig
# ----------------------
class SchemaColumnValueInline(GenericTabularInline):
    model = SchemaColumnValue
    extra = 0
    fields = ("column", "value", "is_edited")
    readonly_fields = ("is_edited",)
    autocomplete_fields = ("column",)


@admin.register(SchemaColumnValue)
class SchemaColumnValueAdmin(admin.ModelAdmin):
    list_display = ("id", "column", "account", "value", "is_edited")
    list_filter = ("column__schema", "is_edited")
    search_fields = ("column__title",)
    autocomplete_fields = ("column",)
    actions = ("reset_overrides",)

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
