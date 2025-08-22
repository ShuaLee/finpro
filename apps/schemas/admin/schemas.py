from django.contrib import admin
from schemas.models import (
    Schema,
    SchemaColumn,
    SchemaColumnValue,
    SchemaColumnTemplate,
    SchemaColumnVisibility,
    SubPortfolioSchemaLink,
    CustomAssetSchemaConfig,
)


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "schema_type", "content_type", "created_at")
    search_fields = ("name", "schema_type")
    list_filter = ("schema_type", "content_type")
    readonly_fields = ("created_at",)


@admin.register(SchemaColumn)
class SchemaColumnAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "schema", "source",
                    "data_type", "display_order", "is_system")
    list_filter = ("source", "data_type", "is_system")
    search_fields = ("title", "schema__name")
    autocomplete_fields = ["schema"]
    readonly_fields = ("created_at",)


@admin.register(SchemaColumnTemplate)
class SchemaColumnTemplateAdmin(admin.ModelAdmin):
    list_display = ["get_account_model_name", "title",
                    "source", "source_field", "data_type", "is_default"]
    list_filter = ["source", "is_default", "is_system"]
    search_fields = ["title", "source_field"]
    ordering = ["display_order"]
    readonly_fields = ("created_at",)

    fieldsets = (
        (None, {
            "fields": (
                "title",
                "source", "source_field",
                "data_type", "field_path",
                "editable", "is_default", "is_deletable", "is_system",
                "formula_method", "formula_expression",
                "constraints",
                "display_order", "investment_theme", "created_at"
            )
        }),
    )

    @admin.display(description="Account Model")
    def get_account_model_name(self, obj):
        return obj.account_model_ct.model_class().__name__ if obj.account_model_ct else "-"


@admin.register(SchemaColumnValue)
class SchemaColumnValueAdmin(admin.ModelAdmin):
    list_display = ("id", "column", "holding", "value")
    search_fields = ("column__title",)
    autocomplete_fields = ("column",)
    list_filter = ("column__schema",)


@admin.register(SchemaColumnVisibility)
class SchemaColumnVisibilityAdmin(admin.ModelAdmin):
    list_display = ("id", "column", "account", "is_visible")
    list_filter = ("is_visible", "column__schema")
    search_fields = ("column__title",)
    autocomplete_fields = ("column",)


@admin.register(SubPortfolioSchemaLink)
class SubPortfolioSchemaLinkAdmin(admin.ModelAdmin):
    list_display = ("id", "subportfolio", "account_model", "schema")
    list_filter = ("schema__schema_type",)
    autocomplete_fields = ("schema",)
    search_fields = ("subportfolio_id", "account_model_id")


@admin.register(CustomAssetSchemaConfig)
class CustomAssetSchemaConfigAdmin(admin.ModelAdmin):
    list_display = ['asset_type', 'created_at', 'updated_at']
    search_fields = ['asset_type']
