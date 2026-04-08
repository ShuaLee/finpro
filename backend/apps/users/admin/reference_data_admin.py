from django.contrib import admin

from apps.users.models import SupportedCountry, SupportedCurrency


@admin.register(SupportedCountry)
class SupportedCountryAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(SupportedCurrency)
class SupportedCurrencyAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    readonly_fields = ("created_at", "updated_at")
