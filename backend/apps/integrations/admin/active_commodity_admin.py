from django.contrib import admin

from apps.integrations.models import ActiveCommodityListing


@admin.register(ActiveCommodityListing)
class ActiveCommodityListingAdmin(admin.ModelAdmin):
    list_display = ("symbol", "name", "exchange", "currency", "provider", "last_refreshed_at")
    list_filter = ("provider", "exchange", "currency")
    search_fields = ("symbol", "name")
    readonly_fields = ("last_refreshed_at", "source_payload")
    ordering = ("symbol",)
    list_per_page = 100

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "provider",
                    "symbol",
                    "name",
                    "exchange",
                    "trade_month",
                    "currency",
                    "last_refreshed_at",
                ),
            },
        ),
        (
            "Raw Payload",
            {
                "fields": ("source_payload",),
            },
        ),
    )
