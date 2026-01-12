from django.contrib import admin
from assets.models.core import AssetPrice


@admin.register(AssetPrice)
class AssetPriceAdmin(admin.ModelAdmin):
    list_display = ("asset", "price", "source", "last_updated")
    list_filter = ("source",)
    search_fields = ("asset__id",)
    readonly_fields = ("last_updated",)
