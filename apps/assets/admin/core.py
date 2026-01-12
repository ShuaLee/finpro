from django.contrib import admin
from assets.models.core import Asset, AssetType


@admin.register(AssetType)
class AssetTypeAdmin(admin.ModelAdmin):
    list_display = ("slug",)
    search_fields = ("slug",)
    ordering = ("slug",)
    readonly_fields = ("slug",)


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("id", "asset_type", "created_at")
    list_filter = ("asset_type",)
    search_fields = ("id",)
    readonly_fields = ("id", "created_at", "updated_at")
