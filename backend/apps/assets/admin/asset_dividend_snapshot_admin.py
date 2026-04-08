from django.contrib import admin

from apps.assets.models import AssetDividendSnapshot


@admin.register(AssetDividendSnapshot)
class AssetDividendSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "asset",
        "status",
        "cadence_status",
        "last_dividend_amount",
        "last_dividend_date",
        "trailing_12m_dividend",
        "forward_annual_dividend",
        "last_computed_at",
    )
    list_filter = ("status", "cadence_status")
    search_fields = ("asset__name", "asset__symbol")
    readonly_fields = ("last_computed_at", "created_at", "updated_at")

    fieldsets = (
        (
            None,
            {
                "fields": ("asset", "status", "cadence_status"),
            },
        ),
        (
            "Last Dividend",
            {
                "fields": (
                    "last_dividend_amount",
                    "last_dividend_date",
                    "last_dividend_frequency",
                    "last_dividend_is_special",
                ),
            },
        ),
        (
            "Regular Dividend",
            {
                "fields": (
                    "regular_dividend_amount",
                    "regular_dividend_date",
                    "regular_dividend_frequency",
                ),
            },
        ),
        (
            "Derived Metrics",
            {
                "fields": (
                    "trailing_12m_dividend",
                    "trailing_12m_cashflow",
                    "forward_annual_dividend",
                    "trailing_dividend_yield",
                    "forward_dividend_yield",
                ),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("last_computed_at", "created_at", "updated_at"),
            },
        ),
    )
