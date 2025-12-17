from django.contrib import admin
from assets.models.classifications.industry import Industry


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_system", "owner")
    list_filter = ("is_system",)
    search_fields = ("name",)
