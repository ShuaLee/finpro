from django.contrib import admin
from django.core.exceptions import PermissionDenied

from formulas.models.formula import Formula
from formulas.models.formula_definition import FormulaDefinition


# ============================================================
# FORMULA ADMIN
# ============================================================

@admin.register(Formula)
class FormulaAdmin(admin.ModelAdmin):
    list_display = (
        "identifier",
        "title",
        "owner",
        "created_at",
    )
    list_filter = ("owner",)
    search_fields = ("identifier", "title", "expression")
    readonly_fields = ("dependencies", "created_at")

    def has_change_permission(self, request, obj=None):
        if obj and obj.owner is None:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.owner is None:
            return False
        return super().has_delete_permission(request, obj)


# ============================================================
# FORMULA DEFINITION ADMIN
# ============================================================

@admin.register(FormulaDefinition)
class FormulaDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        "identifier",
        "asset_type",
        "owner",
        "is_system",
        "dependency_policy",
    )
    list_filter = ("asset_type", "is_system", "owner")
    search_fields = ("identifier", "name", "description")
    readonly_fields = ("created_at",)

    def has_change_permission(self, request, obj=None):
        if obj and obj.is_system:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_system:
            return False
        return super().has_delete_permission(request, obj)
