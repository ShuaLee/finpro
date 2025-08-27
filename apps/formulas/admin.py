from django.contrib import admin
from formulas.models import Formula

# Register your models here.
@admin.register(Formula)
class FormulaAdmin(admin.ModelAdmin):
    list_display = ("key", "title", "is_system", "created_by", "created_at")
    list_filter = ("is_system",)
    search_fields = ("key", "title", "expression")
    readonly_fields = ("created_at", "updated_at")

