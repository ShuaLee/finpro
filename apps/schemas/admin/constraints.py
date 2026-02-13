from django.contrib import admin

from schemas.models import MasterConstraint, SchemaConstraint
from schemas.models.account_column_visibility import AccountColumnVisibility
from schemas.services.mutations import SchemaMutationService


@admin.register(MasterConstraint)
class MasterConstraintAdmin(admin.ModelAdmin):
    list_display = ("name", "label", "applies_to")
    list_filter = ("applies_to",)
    search_fields = ("name", "label")


@admin.register(SchemaConstraint)
class SchemaConstraintAdmin(admin.ModelAdmin):
    list_display = ("column", "name", "applies_to", "is_editable")
    list_filter = ("applies_to", "is_editable")
    search_fields = ("column__identifier", "name")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.save()
            return

        SchemaMutationService.update_constraint(
            constraint=obj,
            changed_fields=list(form.changed_data),
        )


@admin.register(AccountColumnVisibility)
class AccountColumnVisibilityAdmin(admin.ModelAdmin):
    list_display = ("id", "account", "column", "is_visible")
    list_filter = ("is_visible", "account__account_type")
    search_fields = ("account__name", "column__identifier", "column__title")
    list_editable = ("is_visible",)
    ordering = ("account", "column__display_order")
