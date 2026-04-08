from django.contrib import admin

from apps.integrations.models import ActiveCommodityListing


@admin.register(ActiveCommodityListing)
class ActiveCommodityListingAdmin(admin.ModelAdmin):
    list_display = ("symbol", "name", "exchange", "currency", "provider", "last_refreshed_at")
    list_filter = ("provider", "exchange", "currency")
    search_fields = ("symbol", "name")
    readonly_fields = ("last_refreshed_at",)
