from django.contrib import admin

from assets.models.commodity.precious_metal import PreciousMetalAsset


@admin.register(PreciousMetalAsset)
class PreciousMetalAssetAdmin(admin.ModelAdmin):
    list_display = (
        "metal",
        "unit",
        "commodity_symbol",
        "display_price",
        "display_currency",
    )

    list_filter = (
        "metal",
        "unit",
    )

    search_fields = (
        "metal",
        "commodity__symbol",
        "commodity__name",
    )

    readonly_fields = (
        "asset",
        "commodity",
        "display_price",
        "display_currency",
    )

    fieldsets = (
        (None, {
            "fields": (
                "asset",
                "metal",
                "unit",
            )
        }),
        ("Pricing (Derived)", {
            "description": (
                "Price and currency are derived from the underlying commodity "
                "and cannot be edited here."
            ),
            "fields": (
                "commodity",
                "display_price",
                "display_currency",
            )
        }),
    )

    # -------------------------------------------------
    # Derived display helpers
    # -------------------------------------------------
    def display_price(self, obj):
        return obj.price or "—"

    display_price.short_description = "Spot Price"

    def display_currency(self, obj):
        return obj.currency.code if obj.currency else "—"

    display_currency.short_description = "Currency"

    def commodity_symbol(self, obj):
        return obj.commodity.symbol

    commodity_symbol.short_description = "Commodity Symbol"
