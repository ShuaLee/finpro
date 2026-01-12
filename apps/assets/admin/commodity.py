from django.contrib import admin
from assets.models.commodity import CommodityAsset


@admin.register(CommodityAsset)
class CommodityAssetAdmin(admin.ModelAdmin):
    list_display = (
        "symbol",
        "name",
        "currency",
        "trade_month",
        "last_synced",
    )
    search_fields = ("symbol", "name")
    list_filter = ("currency",)
    readonly_fields = ("last_synced",)
