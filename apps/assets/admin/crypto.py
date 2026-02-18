from django import forms
from django.contrib import admin

from assets.models.core import AssetPrice
from assets.models.crypto import CryptoAsset, CryptoSnapshotID


class CryptoAssetAdminForm(forms.ModelForm):
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
        model = CryptoAsset
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and hasattr(self.instance.asset, "price"):
            asset_price = self.instance.asset.price
            self.fields["price"].initial = asset_price.price
            self.fields["price_source"].initial = asset_price.source


@admin.register(CryptoAsset)
class CryptoAssetAdmin(admin.ModelAdmin):
    form = CryptoAssetAdminForm

    list_display = (
        "pair_symbol",
        "base_symbol",
        "currency",
        "display_price",
        "snapshot_id",
    )
    list_filter = ("currency",)
    search_fields = ("pair_symbol", "base_symbol", "name")
    readonly_fields = ("snapshot_id",)

    fieldsets = (
        (None, {"fields": ("name", "pair_symbol", "base_symbol", "currency")}),
        ("Supply", {"fields": ("circulating_supply", "total_supply")}),
        ("Valuation", {"fields": ("price", "price_source")}),
        ("Metadata", {"fields": ("ico_date", "snapshot_id")}),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        price = form.cleaned_data.get("price")
        source = form.cleaned_data.get("price_source") or "MANUAL"
        if price is not None:
            AssetPrice.objects.update_or_create(
                asset=obj.asset,
                defaults={"price": price, "source": source},
            )

    def display_price(self, obj):
        if hasattr(obj.asset, "price"):
            return obj.asset.price.price
        return "-"

    display_price.short_description = "Price"


@admin.register(CryptoSnapshotID)
class CryptoSnapshotIDAdmin(admin.ModelAdmin):
    list_display = ("current_snapshot",)
