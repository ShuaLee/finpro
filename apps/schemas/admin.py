from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from schemas.models import (
    Schema,
    SchemaColumn,
    SchemaColumnValue,
    SchemaColumnVisibility,
    CustomAssetSchemaConfig,
)
from apps.schemas.services.holding_sync_service import sync_schema_column_to_holdings


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "schema_type", "content_type", "object_id", "created_at")
    search_fields = ("name", "schema_type")
    list_filter = ("schema_type", "content_type")
    readonly_fields = ("created_at",)


@admin.register(SchemaColumn)
class SchemaColumnAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'schema', 'title', 'custom_title', 'source', 'source_field',
        'data_type', 'decimal_places', 'editable', 'is_deletable',
        'is_system', 'scope', 'display_order', 'investment_theme',
    )
    list_filter = ('source', 'data_type', 'editable', 'is_deletable', 'is_system', 'scope')
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
            )
        }),
    )

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
