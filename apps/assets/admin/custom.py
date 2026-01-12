from django.contrib import admin
from assets.models.custom import CustomAsset, CustomAssetType


@admin.register(CustomAssetType)
class CustomAssetTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by")
    search_fields = ("name",)
    list_filter = ("created_by",)


@admin.register(CustomAsset)
class CustomAssetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "custom_type",
        "estimated_value",
        "currency",
        "last_updated",
    )
    search_fields = ("name",)
    list_filter = ("currency", "custom_type")
    readonly_fields = ("last_updated",)
