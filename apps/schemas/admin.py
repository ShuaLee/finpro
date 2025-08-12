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


class DisabledOptionSelect(forms.Select):
    """Select that allows disabling some options."""

    def __init__(self, *args, disabled_values=None, **kwargs):
        self.disabled_values = set(disabled_values or [])
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected,
                                       index, subindex=subindex, attrs=attrs)
        # Support optgroups: value may be None for group labels.
        if value in self.disabled_values:
            option['attrs']['disabled'] = True
        return option


class AddBuiltInColumnGlobalForm(forms.Form):
    schema = forms.ModelChoiceField(
        queryset=Schema.objects.all(), required=True, label="Schema")
    catalog_item = forms.ChoiceField(label="Built-in column", required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        schema_obj = None
        # support initial(schema=obj) or posted schema id
        sid = self.data.get("schema") or getattr(
            self.initial.get("schema", None), "pk", None)
        if sid:
            schema_obj = Schema.objects.filter(pk=sid).first()
            if schema_obj:
                self.fields["schema"].initial = schema_obj

        choices, disabled = [], set()
        if schema_obj:
            config = (SCHEMA_CONFIG_REGISTRY.get(schema_obj.schema_type)
                      or SCHEMA_CONFIG_REGISTRY.get(f"{schema_obj.schema_type}_self_managed"))

            if config:
                existing = {
                    f"{c.source}:{c.source_field}"
                    for c in schema_obj.columns.exclude(source__isnull=True).exclude(source_field__isnull=True)
                }
                for group_label, fields in config.items():
                    group = []
                    for source_field, spec in fields.items():
                        key = f"{group_label}:{source_field}"
                        label = spec.get(
                            "title", source_field.replace("_", " ").title())
                        group.append((key, label))
                        if key in existing:
                            disabled.add(key)
                    if group:
                        choices.append((group_label.title(), group))

        self.fields["catalog_item"].widget = DisabledOptionSelect(
            disabled_values=disabled)
        self.fields["catalog_item"].choices = choices

    def create_column(self):
        schema = self.cleaned_data["schema"]
        key = self.cleaned_data["catalog_item"]
        source, source_field = key.split(":", 1)

        config = (SCHEMA_CONFIG_REGISTRY.get(schema.schema_type)
                  or SCHEMA_CONFIG_REGISTRY.get(f"{schema.schema_type}_self_managed"))
        spec = config[source][source_field]

        max_order = SchemaColumn.objects.filter(schema=schema).aggregate(
            models.Max("display_order"))["display_order__max"] or 0

        col, created = SchemaColumn.objects.get_or_create(
            schema=schema,
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
                "display_order": max_order + 1,
                "formula_method": spec.get("formula_method"),
                "formula_expression": spec.get("formula"),
            }
        )
        return col, created


class AddBuiltInColumnForm(forms.Form):
    catalog_item = forms.ChoiceField(label="Built-in column")

    def __init__(self, *args, schema: Schema, **kwargs):
        super().__init__(*args, **kwargs)
        self.schema = schema

        # Pick the right config based on schema_type
        schema_type = schema.schema_type
        config = SCHEMA_CONFIG_REGISTRY.get(
            schema_type) or SCHEMA_CONFIG_REGISTRY.get(f"{schema_type}_self_managed")

        # Build a set of keys already present in this schema: "source:source_field"
        existing = set()
        for c in schema.columns.all():
            if c.source and c.source_field:
                existing.add(f"{c.source}:{c.source_field}")

        # Build grouped choices
        choices = []
        disabled = set()
        if config:
            for group_label, fields in config.items():
                group_options = []
                for source_field, spec in fields.items():
                    key = f"{group_label}:{source_field}"
                    label = spec.get(
                        "title", source_field.replace("_", " ").title())
                    group_options.append((key, label))
                    if key in existing:
                        disabled.add(key)
                if group_options:
                    choices.append((group_label.title(), group_options))

        widget = DisabledOptionSelect(disabled_values=disabled)
        self.fields['catalog_item'].widget = widget
        self.fields['catalog_item'].choices = choices

    def create_column(self):
        """Create the selected SchemaColumn from config."""
        key = self.cleaned_data['catalog_item']
        source, source_field = key.split(":", 1)

        config = SCHEMA_CONFIG_REGISTRY.get(self.schema.schema_type) or SCHEMA_CONFIG_REGISTRY.get(
            f"{self.schema.schema_type}_self_managed")
        spec = config[source][source_field]

        # Create with safe defaults; mark as system
        obj, created = SchemaColumn.objects.get_or_create(
            schema=self.schema,
            source=source,
            source_field=source_field,
            defaults={
                "title": spec["title"],
                "data_type": spec["data_type"],
                "field_path": spec.get("field_path"),
                "decimal_places": spec.get("decimal_places"),
                # value editability
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
    # Extra (non-model) field to pick from config
    built_in = forms.ChoiceField(label="Built-in column", required=False)

    class Meta:
        model = SchemaColumn
        # Do NOT include 'built_in' here; it's extra (non-model) form field
        fields = (
            "custom_title",                # we want this editable
            "title", "data_type", "decimal_places",
            "source", "source_field", "field_path",
            "editable", "is_deletable",
            "is_system", "scope",
            "display_order", "investment_theme",
        )

    # These are set by the inline at runtime (see get_formset)
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

        # EXISTING row behavior
        if inst and inst.pk:
            # System rows: lock structure; only allow custom_title
            if inst.is_system:
                keep = {"custom_title"}
                for name, field in self.fields.items():
                    if name not in keep:
                        field.disabled = True
                # hide the selector on existing rows
                self.fields['built_in'].widget = forms.HiddenInput()
            else:
                # Non-system existing rows: show everything as normal, but hide selector
                self.fields['built_in'].widget = forms.HiddenInput()
        else:
            # NEW row behavior
            # Let the user either pick a built-in OR enter a custom column manually.
            # To encourage built-ins for MVP, we disable structure inputs until a choice is made.
            for name in ("title", "data_type", "decimal_places", "source", "source_field", "field_path",
                         "editable", "is_deletable", "is_system"):
                if name in self.fields:
                    self.fields[name].disabled = True
            # custom_title stays enabled so they can label the column display

    def clean(self):
        cleaned = super().clean()
        bi = cleaned.get("built_in")
        is_new = not self.instance.pk

        if is_new and bi:
            # prevent adding duplicates even if the option was somehow enabled
            if bi in getattr(self, "_builtin_disabled", set()):
                raise forms.ValidationError(
                    "This built-in column already exists in this schema.")

            source, source_field = bi.split(":", 1)
            spec = self._config[source][source_field]

            # Populate structure from config (and mark as system)
            cleaned["source"] = source
            cleaned["source_field"] = source_field
            cleaned["title"] = spec["title"]
            cleaned["data_type"] = spec["data_type"]
            cleaned["field_path"] = spec.get("field_path")
            cleaned["decimal_places"] = spec.get("decimal_places")
            cleaned["editable"] = spec.get(
                "editable", False)          # value editability
            cleaned["is_deletable"] = spec.get("is_deletable", False)
            cleaned["is_system"] = spec.get("is_system", True)
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)

        # If new and built-in selected, ensure display_order is appended
        if not self.instance.pk:
            # parent schema fk is assigned by the inline formset
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
    fields = SchemaColumnInlineForm.Meta.fields
    ordering = ("display_order",)
    show_change_link = True


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "schema_type",
                    "content_type", "object_id", "created_at")
    search_fields = ("name", "schema_type")
    list_filter = ("schema_type", "content_type")
    readonly_fields = ("created_at",)
    inlines = [SchemaColumnInline]
    # custom template with button
    change_form_template = "admin/schemas/schema/change_form.html"

    def save_formset(self, request, form, formset, change):
        instances = formset.save()
        if formset.model is SchemaColumn:
            for obj in getattr(formset, "new_objects", []):
                sync_schema_column_to_holdings(obj)
        return instances

    # Custom URL to add built-in column
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


@admin.register(SchemaColumn)
class SchemaColumnAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'schema', 'title', 'custom_title', 'source', 'source_field',
        'data_type', 'decimal_places', 'editable', 'is_deletable',
        'is_system', 'scope', 'display_order', 'investment_theme',
    )
    list_filter = ('schema', 'source', 'data_type', 'editable',
                   'is_deletable', 'is_system', 'scope')  # added 'schema'
    search_fields = ('title', 'custom_title', 'source_field')
    raw_id_fields = ('schema', 'investment_theme',)
    # <- add button on list page
    change_list_template = "admin/schemas/schemacolumn/change_list.html"

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

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if obj and obj.is_system:
            ro += ['data_type', 'decimal_places',
                   'source', 'source_field', 'field_path']
        return ro

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        if is_new:
            sync_schema_column_to_holdings(obj)

    # --- custom URL + view for "Add built-in column" ---
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("add_builtin/", self.admin_site.admin_view(self.add_builtin_view),
                 name="schemas_schemacolumn_add_builtin"),
        ]
        return custom + urls

    def add_builtin_view(self, request):
        initial = {}
        sid = request.GET.get("schema") or request.GET.get("schema__id__exact")
        if sid:
            schema = Schema.objects.filter(pk=sid).first()
            if schema:
                initial["schema"] = schema

        if request.method == "POST":
            form = AddBuiltInColumnGlobalForm(
                request.POST, initial=initial)  # ← swap here
            if form.is_valid():
                col, created = form.create_column()
                if created:
                    sync_schema_column_to_holdings(col)
                    messages.success(
                        request, f'Added built-in column “{col.title}”.')
                else:
                    messages.warning(
                        request, "That column already exists in this schema.")
                url = reverse("admin:schemas_schemacolumn_changelist") + \
                    f"?schema__id__exact={col.schema_id}"
                return redirect(url)
        else:
            form = AddBuiltInColumnGlobalForm(initial=initial)  # ← and here

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Add built-in column",
            "form": form,
            "media": self.media + form.media,
        }
        return TemplateResponse(request, "admin/schemas/schemacolumn/add_builtin.html", context)


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
