from django.contrib import admin
from assets.models.market_data_cache import MarketDataCache


@admin.register(MarketDataCache)
class MarketDataCacheAdmin(admin.ModelAdmin):
    list_display = (
        "asset", "last_price", "pe_ratio", "eps",
        "dividend_yield", "market_cap", "last_synced",
    )
    search_fields = ("asset__name", "asset__identifiers__value")
    readonly_fields = ("asset",)
    list_filter = ("asset__equity_detail__exchange",)
