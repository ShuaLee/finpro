from django.contrib import admin
from schemas.models import SchemaColumnTemplate


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
