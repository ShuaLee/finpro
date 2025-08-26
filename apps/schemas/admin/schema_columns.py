from django.contrib import admin
from schemas.models import (
    SchemaColumn,

)


@admin.register(SchemaColumn)
class SchemaColumnAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "schema", "source",
                    "data_type", "display_order", "is_system")
    list_filter = ("source", "data_type", "is_system", "schema")
    search_fields = ("title", "schema__name")
    autocomplete_fields = ["schema"]
    readonly_fields = ("created_at",)

    def get_readonly_fields(self, request, obj=None):
        base = super().get_readonly_fields(request, obj)
        readonly = (
            "display_order",  # Always readonly
            "title", "schema", "data_type", "source", "source_field",
            "field_path", "constraints", "formula_method",
            "formula_expression", "is_system", "is_editable", "is_deletable", "created_at"
        )
        if obj and obj.is_system:
            return base + readonly
        return base + ("display_order",)
