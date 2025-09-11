from django import forms
from django.core.exceptions import ValidationError
from django.contrib import admin, messages
from assets.models.proxies import MetalAsset
from assets.models.details.metal_detail import MetalDetail
from assets.services.asset_sync import AssetSyncService
from apps.external_data.fmp.dispatch import detect_asset_type


class MetalAddForm(forms.ModelForm):
    class Meta:
        model = MetalAsset
        fields = ["symbol"]

    def clean_symbol(self):
        symbol = self.cleaned_data["symbol"].upper()
        detected_type = detect_asset_type(symbol)
        if detected_type != "metal":
            raise ValidationError(
                f"❌ {symbol} is not a Metal (detected type: {detected_type})."
            )
        return symbol


class MetalDetailInline(admin.StackedInline):
    model = MetalDetail
    can_delete = False
    extra = 0


@admin.register(MetalAsset)
class MetalAssetAdmin(admin.ModelAdmin):
    form = MetalAddForm
    list_display = ("id", "symbol", "name", "created_at")
    search_fields = ("symbol", "name")
    list_filter = ("metal_detail__currency",)
    inlines = [MetalDetailInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("metal_detail")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if AssetSyncService.sync(obj):
            self.message_user(request, f"✅ Synced {obj.symbol} successfully.", messages.SUCCESS)
        else:
            self.message_user(request, f"⚠️ Added {obj.symbol}, but sync failed/custom.", messages.WARNING)
