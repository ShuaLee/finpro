from django.contrib import admin
from schemas.models import SchemaColumnTemplate


@admin.register(SchemaColumnTemplate)
class SchemaColumnTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "asset_type",
        "title",
        "source",
        "source_field",
        "data_type",
        "is_system",
        "is_default",
        "is_deletable",
        "display_order",
    )
    list_filter = ("asset_type", "source", "is_system", "is_default")
    search_fields = ("title", "source_field", "formula_method")
    ordering = ("asset_type", "display_order")

    readonly_fields = ("created_at",)

    fieldsets = (
        (None, {
            "fields": (
                "asset_type",
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
