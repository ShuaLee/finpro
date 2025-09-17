from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from assets.models.proxies import EquityAsset
from assets.models.details.equity_detail import EquityDetail
from assets.services.syncs.asset_sync import AssetSyncService
from external_data.fmp.dispatch import fetch_asset_data


class EquityAddForm(forms.ModelForm):
    class Meta:
        model = EquityAsset
        fields = ["symbol"]

    def clean_symbol(self):
        symbol = self.cleaned_data["symbol"].upper()
        detected_type = fetch_asset_data(symbol)
        if detected_type != "equity":
            raise ValidationError(
                f"Symbol {symbol} is not an Equity (detected type: {detected_type})."
            )
        return symbol


class EquityDetailInline(admin.StackedInline):
    model = EquityDetail
    can_delete = False
    extra = 0


@admin.register(EquityAsset)
class EquityAssetAdmin(admin.ModelAdmin):
    form = EquityAddForm
    list_display = ("id", "symbol", "name", "created_at")
    search_fields = ("symbol", "name", "equity_detail__isin",
                     "equity_detail__cusip")
    list_filter = ("equity_detail__exchange", "equity_detail__sector")
    inlines = [EquityDetailInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("equity_detail")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if AssetSyncService.sync(obj):
            self.message_user(
                request, f"✅ Synced {obj.symbol} successfully.", messages.SUCCESS)
        else:
            self.message_user(
                request, f"⚠️ Added {obj.symbol}, but sync failed/custom.", messages.WARNING)
