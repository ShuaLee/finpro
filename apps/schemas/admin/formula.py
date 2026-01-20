from django.contrib import admin
from schemas.models.formula import Formula


@admin.register(Formula)
class FormulaAdmin(admin.ModelAdmin):
    list_display = ("identifier", "title", "decimal_places",
                    "is_system", "updated_at")
    search_fields = ("identifier", "title")
    readonly_fields = ("dependencies",)
    list_filter = ("is_system",)
