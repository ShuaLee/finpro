from django.contrib import admin

from apps.assets.models import AssetMarketData


@admin.register(AssetMarketData)
class AssetMarketDataAdmin(admin.ModelAdmin):
    list_display = (
        "asset",
        "provider",
        "provider_symbol",
        "status",
        "last_synced_at",
        "last_successful_sync_at",
        "updated_at",
    )
    list_filter = ("provider", "status")
    search_fields = ("asset__name", "asset__symbol", "provider_symbol", "provider_identifier")
    readonly_fields = ("created_at", "updated_at")
