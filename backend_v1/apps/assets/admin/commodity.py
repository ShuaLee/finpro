from django import forms
from django.contrib import admin

from assets.models.core import AssetPrice
from assets.models.commodity import (
    CommodityAsset,
    CommoditySnapshotID,
)


# =================================================
# Forms
# =================================================

class CommodityAssetAdminForm(forms.ModelForm):
    """
    Admin form exposing AssetPrice for commodity assets.
    """

    price = forms.DecimalField(
        max_digits=20,
        decimal_places=8,
        required=False,
        help_text="Current market price (manual override).",
    )

    price_source = forms.CharField(
        max_length=50,
        required=False,
        initial="MANUAL",
    )

    class Meta:
        model = CommodityAsset
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk and hasattr(self.instance.asset, "price"):
            asset_price = self.instance.asset.price
            self.fields["price"].initial = asset_price.price
            self.fields["price_source"].initial = asset_price.source


# =================================================
# Admin
# =================================================

@admin.register(CommodityAsset)
class CommodityAssetAdmin(admin.ModelAdmin):
    form = CommodityAssetAdminForm

    list_display = (
        "symbol",
        "name",
        "currency",
        "display_price",
        "trade_month",
        "snapshot_id",
    )

    list_filter = (
        "currency",
        "trade_month",
    )

    search_fields = (
        "symbol",
        "name",
    )

    readonly_fields = (
        "snapshot_id",
    )

    fieldsets = (
        (None, {
            "fields": (
                "name",
                "symbol",
                "currency",
            )
        }),
        ("Contract Metadata", {
            "fields": (
                "exchange",
                "trade_month",
            )
        }),
        ("Valuation", {
            "fields": (
                "price",
                "price_source",
            )
        }),
        ("Snapshot", {
            "fields": (
                "snapshot_id",
            )
        }),
    )

    # -------------------------------------------------
    # Save hooks
    # -------------------------------------------------
    def save_model(self, request, obj, form, change):
        """
        Persist CommodityAsset AND AssetPrice.
        """
        super().save_model(request, obj, form, change)

        price = form.cleaned_data.get("price")
        source = form.cleaned_data.get("price_source") or "MANUAL"

        if price is not None:
            AssetPrice.objects.update_or_create(
                asset=obj.asset,
                defaults={
                    "price": price,
                    "source": source,
                },
            )

    # -------------------------------------------------
    # Derived display helpers
    # -------------------------------------------------
    def display_price(self, obj):
        if hasattr(obj.asset, "price"):
            return obj.asset.price.price
        return "—"

    display_price.short_description = "Price"


@admin.register(CommoditySnapshotID)
class CommoditySnapshotIDAdmin(admin.ModelAdmin):
    list_display = ("current_snapshot",)
