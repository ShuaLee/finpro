from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from schemas.models import (
    Schema,
    SchemaColumn,
    SchemaColumnValue,
    SchemaColumnVisibility,
    CustomAssetSchemaConfig
)
from apps.schemas.services.holding_sync_service import sync_schema_column_to_holdings


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("name", "schema_type", "content_type",
                    "object_id", "created_at")
    search_fields = ("name", "schema_type")
    list_filter = ("schema_type", "content_type")
    readonly_fields = ("created_at",)


@admin.register(SchemaColumn)
class SchemaColumnAdmin(admin.ModelAdmin):
    list_display = ("title", "schema", "source",
                    "source_field", "editable", "is_deletable")
    list_filter = ("source", "editable", "is_deletable")
    search_fields = ("title", "source_field", "schema__name")
    readonly_fields = ("schema",)

    fieldsets = (
        (None, {
            "fields": (
                "schema", "title", "data_type", "source", "source_field",
                "formula", "formula_expression",
                "editable", "is_deletable", "decimal_places", "is_system", "scope"
            )
        }),
    )

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)

        if is_new:
            sync_schema_column_to_holdings(obj)


class SchemaColumnValueInline(GenericTabularInline):
    model = SchemaColumnValue
    extra = 0
    fields = ("column", "value", "is_edited")
    readonly_fields = ("is_edited",)
    autocomplete_fields = ("column",)


@admin.register(SchemaColumnValue)
class SchemaColumnValueAdmin(admin.ModelAdmin):
    list_display = ("column", "account", "value", "is_edited")
    list_filter = ("column__schema", "is_edited")
    search_fields = ("column__title", "account__name")
    autocomplete_fields = ("column",)


@admin.register(SchemaColumnVisibility)
class SchemaColumnVisibilityAdmin(admin.ModelAdmin):
    list_display = ("column", "account", "is_visible")
    list_filter = ("is_visible", "column__schema")
    search_fields = ("column__title",)
    autocomplete_fields = ("column",)


@admin.register(CustomAssetSchemaConfig)
class AssetSchemaConfigAdmin(admin.ModelAdmin):
    list_display = ['asset_type', 'created_at', 'updated_at']
    search_fields = ['asset_type']
