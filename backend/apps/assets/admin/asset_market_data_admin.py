from django.contrib import admin

from apps.assets.models import AssetMarketData


@admin.register(AssetMarketData)
class AssetMarketDataAdmin(admin.ModelAdmin):
    list_display = (
        "asset",
        "provider",
        "provider_symbol",
        "isin",
        "cusip",
        "cik",
        "status",
        "last_synced_at",
        "last_successful_sync_at",
        "updated_at",
    )
    list_filter = ("provider", "status")
    search_fields = (
        "asset__name",
        "asset__symbol",
        "provider_symbol",
        "provider_identifier",
        "isin",
        "cusip",
        "cik",
    )
    readonly_fields = ("created_at", "updated_at")
    ordering = ("asset__name",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "asset",
                    "provider",
                    "status",
                ),
            },
        ),
        (
            "Provider Identity",
            {
                "fields": (
                    "provider_symbol",
                    "provider_identifier",
                    "isin",
                    "cusip",
                    "cik",
                ),
            },
        ),
        (
            "Last Seen",
            {
                "fields": (
                    "last_seen_symbol",
                    "last_seen_name",
                    "last_seen_exchange",
                ),
            },
        ),
        (
            "Sync State",
            {
                "fields": (
                    "last_synced_at",
                    "last_successful_sync_at",
                    "last_error",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )
