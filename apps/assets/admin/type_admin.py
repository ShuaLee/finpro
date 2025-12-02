from django.contrib import admin
from assets.models import RealEstateType


@admin.register(RealEstateType)
class RealEstateTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_custom")
    list_filter = ("is_custom",)
    search_fields = ("name",)
