from django.contrib import admin

from schemas.models import SchemaColumn
from schemas.models.schema_column_asset_behaviour import SchemaColumnAssetBehaviour
from schemas.services.mutations import SchemaMutationService


@admin.register(SchemaColumn)
class SchemaColumnAdmin(admin.ModelAdmin):
    list_display = (
        "identifier",
        "schema",
        "data_type",
        "is_system",
        "is_editable",
        "is_deletable",
    )
    list_filter = ("data_type", "is_system")
    search_fields = ("identifier",)
    ordering = ("schema", "display_order")
    readonly_fields = ("identifier", "schema", "is_system")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change:
            SchemaMutationService.update_column(
                column=obj,
                changed_fields=list(form.changed_data),
            )

    def delete_model(self, request, obj):
        SchemaMutationService.delete_column(obj)

    def delete_queryset(self, request, queryset):
        for column in queryset:
            SchemaMutationService.delete_column(column)

    def has_delete_permission(self, request, obj=None):
        if obj and not obj.is_deletable:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(SchemaColumnAssetBehaviour)
class SchemaColumnAssetBehaviourAdmin(admin.ModelAdmin):
    list_display = ("column", "asset_type", "source",
                    "formula_definition", "is_override")
    list_filter = ("asset_type", "source", "is_override")
    search_fields = ("column__identifier", "formula_definition__identifier")
