from django.contrib import admin
from django.utils.text import slugify
from schemas.models import (
    SchemaColumn,
)
from schemas.services.holding_sync_service import sync_schema_column_to_holdings, delete_column_values
from .forms import SchemaColumnCustomAddForm


@admin.register(SchemaColumn)
class SchemaColumnAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'schema', 'title', 'custom_title', 'source', 'source_field',
        'data_type', 'editable', 'is_deletable',
        'is_system', 'scope', 'display_order', 'investment_theme',
    )
    list_filter = ('schema', 'source', 'data_type', 'editable',
                   'is_deletable', 'is_system', 'scope')
    search_fields = ('title', 'custom_title', 'source_field')
    raw_id_fields = ('investment_theme',)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs["form"] = SchemaColumnCustomAddForm
        form_class = super().get_form(request, obj, **kwargs)
        # Assert to catch shadowing/incorrect form
        if "data_type" not in form_class.base_fields:
            raise Exception(
                "SchemaColumnCustomAddForm not applied or data_type not present.")
        return form_class

    def get_fieldsets(self, request, obj=None):
        base_fields = (
            "schema",
            "title",
            ("data_type",),
            "editable",
            ("scope", "display_order"),
            "investment_theme",
        )
        constraints_fields = (
            ("Constraints", {
                "fields": (
                    # decimal/number
                    ("dec_min", "dec_max"),
                    ("character_minimum", "character_limit", "all_caps"),  # string
                )
            }),
        )
        if obj is None or (obj and obj.source == "custom"):
            return ((None, {"fields": base_fields}),) + constraints_fields

        return ((None, {
            "fields": (
                "schema",
                ("title", "custom_title"),
                ("data_type",),
                ("source", "source_field", "field_path"),
                ("formula_method", "formula_expression"),
                ("editable", "is_deletable"),
                ("is_system", "scope", "display_order"),
                "investment_theme",
            )
        }),)

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if obj and obj.source == "custom":
            ro += [
                'is_deletable', 'is_system', 'source', 'source_field',
                'field_path', 'formula_method', 'formula_expression', 'custom_title'
            ]
        elif obj and obj.is_system:
            ro += ['data_type', 'source',
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

    def delete_model(self, request, obj):
        delete_column_values(obj)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            delete_column_values(obj)
        super().delete_queryset(request, queryset)
