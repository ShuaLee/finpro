from django.contrib import admin
from fx.models.country import Country
from fx.models.fx import FXCurrency, FXRate


@admin.register(FXCurrency)
class FXCurrencyAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "created_at")
    search_fields = ("code", "name")


@admin.register(FXRate)
class FXRateAdmin(admin.ModelAdmin):
    list_display = ("from_currency", "to_currency", "rate", "updated_at")
    search_fields = ("from_currency__code", "to_currency__code")
    list_filter = ("from_currency__code", "to_currency__code")


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "region", "updated_at")
    list_filter = ("region",)
    search_fields = ("code", "name")
    ordering = ("code",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Country Info", {
            "fields": ("code", "name", "region")
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
