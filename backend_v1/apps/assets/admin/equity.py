from django.contrib import admin
from assets.models.equity import (
    EquityAsset,
    Exchange,
    EquityDividendSnapshot,
    EquitySnapshotID,
)


@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "country")
    search_fields = ("code", "name")
    list_filter = ("country",)


@admin.register(EquityAsset)
class EquityAssetAdmin(admin.ModelAdmin):
    list_display = (
        "ticker",
        "name",
        "exchange",
        "country",
        "currency",
        "snapshot_id",
    )
    list_filter = ("exchange", "country", "currency", "snapshot_id")
    search_fields = ("ticker", "name")
    ordering = ("ticker",)
    readonly_fields = ("snapshot_id",)


@admin.register(EquityDividendSnapshot)
class EquityDividendSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "asset",
        "last_dividend_amount",
        "regular_dividend_amount",
        "trailing_12m_dividend",
        "forward_annual_dividend",
        "status",
        "last_computed",
    )
    list_filter = ("status",)
    search_fields = ("asset__id",)
    readonly_fields = ("last_computed",)


@admin.register(EquitySnapshotID)
class EquitySnapshotIDAdmin(admin.ModelAdmin):
    list_display = ("id", "current_snapshot")
    readonly_fields = ("id",)
