from django.contrib import admin
from fx.models import FXCurrency, FXRate


@admin.register(FXCurrency)
class FXCurrencyAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "created_at")
    search_fields = ("code", "name")


@admin.register(FXRate)
class FXRateAdmin(admin.ModelAdmin):
    list_display = ("from_currency", "to_currency", "rate", "updated_at")
    search_fields = ("from_currency__code", "to_currency__code")
    list_filter = ("from_currency__code", "to_currency__code")
