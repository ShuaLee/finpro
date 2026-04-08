from django.contrib import admin

from apps.integrations.models import FXRateCache


@admin.register(FXRateCache)
class FXRateCacheAdmin(admin.ModelAdmin):
    list_display = ("base_currency", "quote_currency", "rate", "provider", "pair_symbol", "as_of")
    list_filter = ("provider", "base_currency", "quote_currency")
    search_fields = ("base_currency", "quote_currency", "pair_symbol")
    readonly_fields = ("source_payload", "as_of")
    ordering = ("base_currency", "quote_currency")
