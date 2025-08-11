from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from schemas.models import (
    Schema,
    SchemaColumn,
    SchemaColumnValue,
    SchemaColumnVisibility,
    CustomAssetSchemaConfig,
)
from schemas.services.holding_sync_service import sync_schema_column_to_holdings


class SchemaColumnInline(admin.TabularInline):
    model = SchemaColumn
    extra = 0
    fields = (
        "title", "custom_title",
        "data_type", "decimal_places",
        "source", "source_field", "field_path",
        "editable", "is_deletable",
        "is_system", "scope",
        "display_order", "investment_theme",
        "structure_edit_mode",
    )
    ordering = ("display_order",)
    show_change_link = True

    def get_readonly_fields(self, request, obj=None):
        # obj here is the Schema; rows are instances of SchemaColumn in formset
        ro = []
        # Make all existing rows honor their mode
        if hasattr(self, 'formset') and hasattr(self.formset, 'queryset'):
            pass  # admin inlines don't give row objects here; we rely on model.clean() as the hard stop
        # UI-level comfort: we can still lock by default for system columns
        return ro


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "schema_type",
                    "content_type", "object_id", "created_at")
    search_fields = ("name", "schema_type")
    list_filter = ("schema_type", "content_type")
    readonly_fields = ("created_at",)
    inlines = [SchemaColumnInline]

    # Ensure existing "sync new columns to holdings" also runs when
    # columns are created via the inline (since SchemaColumnValue.save_model wont fire).

    def save_format(self, request, form, formset, change):
        instances = formset.save()
        if formset.model is SchemaColumn:
            for obj in getattr(formset, "new_objects", []):
                sync_schema_column_to_holdings(obj)
        return instances


@admin.register(SchemaColumn)
class SchemaColumnAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'schema', 'title', 'custom_title', 'source', 'source_field',
        'data_type', 'decimal_places', 'editable', 'is_deletable',
        'is_system', 'scope', 'display_order', 'investment_theme',
    )
    list_filter = ('source', 'data_type', 'editable',
                   'is_deletable', 'is_system', 'scope')
    search_fields = ('title', 'custom_title', 'source_field')
    # Was ('schema', 'theme') before — fix to the actual FK name
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
                "theme",  # link to InvestmentTheme if this column represents a theme
                "structure_edit_mode",
            )
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if obj:
            mode = 'locked' if obj.is_system else obj.structure_edit_mode
            if mode in ('locked', 'decimal_only'):
                ro += ['data_type', 'source', 'source_field', 'field_path']
            if mode == 'locked':
                ro += ['decimal_places']
        return ro

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        if is_new:
            # Seed SCVs for all relevant holdings when a new column is created
            sync_schema_column_to_holdings(obj)


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
