from django import forms
from django.core.exceptions import ValidationError
from django.contrib import admin, messages
from assets.models.proxies import BondAsset
from assets.models.details.bond_detail import BondDetail
from assets.services.asset_sync import AssetSyncService
from apps.external_data.fmp.dispatch import detect_asset_type

class BondAddForm(forms.ModelForm):
    class Meta:
        model = BondAsset
        fields = ["symbol"]

    def clean_symbol(self):
        symbol = self.cleaned_data["symbol"].upper()
        detected_type = detect_asset_type(symbol)
        if detected_type != "bond":
            raise ValidationError(
                f"❌ {symbol} is not a Bond (detected type: {detected_type})."
            )
        return symbol



class BondDetailInline(admin.StackedInline):
    model = BondDetail
    can_delete = False
    extra = 0


@admin.register(BondAsset)    # ✅ register proxy
class BondAssetAdmin(admin.ModelAdmin):
    form = BondAddForm
    list_display = ("id", "symbol", "name", "created_at")
    search_fields = ("symbol", "name", "bond_detail__cusip", "bond_detail__isin")
    list_filter = ("bond_detail__country", "bond_detail__bond_type")
    inlines = [BondDetailInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("bond_detail")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if AssetSyncService.sync(obj):
            self.message_user(request, f"✅ Synced {obj.symbol} successfully.", messages.SUCCESS)
        else:
            self.message_user(request, f"⚠️ Added {obj.symbol}, but sync failed/custom.", messages.WARNING)
