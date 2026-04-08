from django.contrib import admin

from apps.integrations.models import ActiveCryptoListing


@admin.register(ActiveCryptoListing)
class ActiveCryptoListingAdmin(admin.ModelAdmin):
    list_display = ("symbol", "name", "base_symbol", "quote_currency", "provider", "last_refreshed_at")
    list_filter = ("provider", "quote_currency")
    search_fields = ("symbol", "name", "base_symbol")
    readonly_fields = ("last_refreshed_at",)
