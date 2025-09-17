from django import forms
from django.core.exceptions import ValidationError
from django.contrib import admin, messages
from assets.models.proxies import CryptoAsset
from assets.models.details.crypto_detail import CryptoDetail
from assets.services.syncs.asset_sync import AssetSyncService
from apps.external_data.fmp.dispatch import fetch_asset_data


class CryptoAddForm(forms.ModelForm):
    class Meta:
        model = CryptoAsset
        fields = ["symbol"]

    def clean_symbol(self):
        symbol = self.cleaned_data["symbol"].upper()
        detected_type = fetch_asset_data(symbol)
        if detected_type != "crypto":
            raise ValidationError(
                f"❌ {symbol} is not a Crypto (detected type: {detected_type})."
            )
        return symbol


class CryptoDetailInline(admin.StackedInline):
    model = CryptoDetail
    can_delete = False
    extra = 0


@admin.register(CryptoAsset)
class CryptoAssetAdmin(admin.ModelAdmin):
    form = CryptoAddForm
    list_display = ("id", "symbol", "name", "created_at")
    search_fields = ("symbol", "name")
    list_filter = ("crypto_detail__currency",)
    inlines = [CryptoDetailInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("crypto_detail")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if AssetSyncService.sync(obj):
            self.message_user(
                request, f"✅ Synced {obj.symbol} successfully.", messages.SUCCESS)
        else:
            self.message_user(
                request, f"⚠️ Added {obj.symbol}, but sync failed/custom.", messages.WARNING)
