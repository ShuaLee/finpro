from django.contrib import admin
from schemas.models.constraints import MasterConstraint, SchemaConstraint


@admin.register(MasterConstraint)
class MasterConstraintAdmin(admin.ModelAdmin):
    list_display = ("applies_to", "name", "label")
    list_filter = ("applies_to",)
    search_fields = ("name", "label")


@admin.register(SchemaConstraint)
class SchemaConstraintAdmin(admin.ModelAdmin):
    list_display = (
        "column", "name", "applies_to", "get_typed_value",
        "get_typed_min", "get_typed_max", "is_editable"
    )
    list_filter = ("applies_to", "is_editable")
    search_fields = ("column__identifier", "name")
