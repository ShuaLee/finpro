from django.contrib import admin
from assets.models import RealEstateType


@admin.register(RealEstateType)
class RealEstateTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_system", "created_by")
    list_filter = ("is_system", "created_by")
    search_fields = ("name",)
