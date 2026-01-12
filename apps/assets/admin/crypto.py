from django.contrib import admin
from assets.models.crypto import CryptoAsset


@admin.register(CryptoAsset)
class CryptoAssetAdmin(admin.ModelAdmin):
    list_display = (
        "base_symbol",
        "pair_symbol",
        "name",
        "currency",
        "circulating_supply",
        "total_supply",
        "last_synced",
    )
    search_fields = ("base_symbol", "pair_symbol", "name")
    list_filter = ("currency",)
    readonly_fields = ("last_synced",)
