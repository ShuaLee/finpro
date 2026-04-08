from django.contrib import admin

from apps.integrations.models import ActiveCryptoListing


@admin.register(ActiveCryptoListing)
class ActiveCryptoListingAdmin(admin.ModelAdmin):
    list_display = ("symbol", "name", "base_symbol", "quote_currency", "provider", "last_refreshed_at")
    list_filter = ("provider", "quote_currency")
    search_fields = ("symbol", "name", "base_symbol")
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
                    "base_symbol",
                    "quote_currency",
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
