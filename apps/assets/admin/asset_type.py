from django.contrib import admin
from assets.models.asset_core import AssetType


@admin.register(AssetType)
class AssetTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_system")
    readonly_fields = ("is_system",)
