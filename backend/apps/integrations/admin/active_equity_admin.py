from django.contrib import admin

from apps.integrations.models import ActiveEquityListing


@admin.register(ActiveEquityListing)
class ActiveEquityListingAdmin(admin.ModelAdmin):
    list_display = ("symbol", "name", "provider", "last_refreshed_at")
    list_filter = ("provider",)
    search_fields = ("symbol", "name")
    readonly_fields = ("last_refreshed_at",)
