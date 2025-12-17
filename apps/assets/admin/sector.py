from django.contrib import admin
from assets.models.classifications.sector import Sector


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ("name", "is_system", "owner")
    list_filter = ("is_system",)
    search_fields = ("name",)
