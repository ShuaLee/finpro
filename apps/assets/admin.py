from django import forms
from django.contrib import admin, messages
from assets.models.asset import Asset
from assets.models.crypto_detail import CryptoDetail
from assets.models.metal_detail import MetalDetail
from assets.models.stock_detail import StockDetail
from assets.services.asset_sync import AssetSyncService


# ------------------------------
# Base Add Form (only symbol)
# ------------------------------
class SymbolAddForm(forms.ModelForm):
    symbol = forms.CharField(
        max_length=20,
        help_text="Enter symbol/ticker (e.g., AAPL, BTCUSD, XAUUSD)",
    )

    class Meta:
        model = Asset
        fields = ["symbol"]  # ✅ only symbol shown


# ------------------------------
# Specialized Add Forms
# ------------------------------
class StockAddForm(SymbolAddForm):
    def save(self, commit=True):
        asset = super().save(commit=False)
        asset.asset_type = "stock"
        asset.name = asset.name or ""
        asset.save()
        AssetSyncService.sync(asset)
        return asset


class CryptoAddForm(SymbolAddForm):
    def save(self, commit=True):
        asset = super().save(commit=False)
        asset.asset_type = "crypto"
        asset.name = asset.name or ""
        asset.save()
        AssetSyncService.sync(asset)
        return asset


class MetalAddForm(SymbolAddForm):
    def save(self, commit=True):
        asset = super().save(commit=False)
        asset.asset_type = "metal"
        asset.name = asset.name or ""
        asset.save()
        AssetSyncService.sync(asset)
        return asset


# ------------------------------
# Inlines for Asset Admin
# ------------------------------
class StockDetailInline(admin.StackedInline):
    model = StockDetail
    can_delete = False
    extra = 0


class CryptoDetailInline(admin.StackedInline):
    model = CryptoDetail
    can_delete = False
    extra = 0


class MetalDetailInline(admin.StackedInline):
    model = MetalDetail
    can_delete = False
    extra = 0


# ------------------------------
# Asset Admin
# ------------------------------
@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("id", "asset_type", "symbol", "name", "created_at", "updated_at")
    list_filter = ("asset_type", "created_at")
    search_fields = ("symbol", "name")

    def get_inlines(self, request, obj=None):
        """Show the right detail inline depending on asset_type."""
        if not obj:
            return []
        if obj.asset_type == "stock":
            return [StockDetailInline]
        elif obj.asset_type == "crypto":
            return [CryptoDetailInline]
        elif obj.asset_type == "metal":
            return [MetalDetailInline]
        return []

    def save_model(self, request, obj, form, change):
        """Sync on save, then show success/failure message."""
        super().save_model(request, obj, form, change)
        success = AssetSyncService.sync(obj)
        if success:
            self.message_user(request, f"Synced {obj.symbol} successfully.", messages.SUCCESS)
        else:
            self.message_user(request, f"Added {obj.symbol} as custom or sync failed.", messages.WARNING)


# ------------------------------
# Detail Admins
# ------------------------------
@admin.register(StockDetail)
class StockDetailAdmin(admin.ModelAdmin):
    list_display = ("asset", "exchange", "sector", "industry", "last_price", "is_custom")
    search_fields = ("asset__symbol", "asset__name")
    list_filter = ("is_custom", "exchange", "sector")


@admin.register(CryptoDetail)
class CryptoDetailAdmin(admin.ModelAdmin):
    list_display = ("asset", "currency", "last_price", "is_custom")
    search_fields = ("asset__symbol", "asset__name")
    list_filter = ("is_custom",)


@admin.register(MetalDetail)
class MetalDetailAdmin(admin.ModelAdmin):
    list_display = ("asset", "currency", "last_price", "is_custom")
    search_fields = ("asset__symbol", "asset__name")
    list_filter = ("is_custom", "currency")
