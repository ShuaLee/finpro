from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path
from assets.models.asset import Asset, AssetType
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
        symbol = self.cleaned_data["symbol"].upper()
        asset, _ = Asset.objects.get_or_create(
            asset_type=AssetType.STOCK,
            symbol=symbol,
            defaults={"name": ""},
        )
        if not AssetSyncService.sync(asset):
            detail, _ = StockDetail.objects.get_or_create(asset=asset)
            detail.is_custom = True
            detail.save()
        return asset


class CryptoAddForm(SymbolAddForm):
    def save(self, commit=True):
        symbol = self.cleaned_data["symbol"].upper()
        asset, _ = Asset.objects.get_or_create(
            asset_type=AssetType.CRYPTO,
            symbol=symbol,
            defaults={"name": ""},
        )
        if not AssetSyncService.sync(asset):
            detail, _ = CryptoDetail.objects.get_or_create(asset=asset)
            detail.is_custom = True
            detail.save()
        return asset


class MetalAddForm(SymbolAddForm):
    def save(self, commit=True):
        symbol = self.cleaned_data["symbol"].upper()
        asset, _ = Asset.objects.get_or_create(
            asset_type=AssetType.METAL,
            symbol=symbol,
            defaults={"name": ""},
        )
        if not AssetSyncService.sync(asset):
            detail, _ = MetalDetail.objects.get_or_create(asset=asset)
            detail.is_custom = True
            detail.save()
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
        if obj:
            if obj.asset_type == AssetType.STOCK:
                return [StockDetailInline]
            elif obj.asset_type == AssetType.CRYPTO:
                return [CryptoDetailInline]
            elif obj.asset_type == AssetType.METAL:
                return [MetalDetailInline]
        return []

    def save_model(self, request, obj, form, change):
        """Sync on save, then show success message."""
        super().save_model(request, obj, form, change)
        success = AssetSyncService.sync(obj)
        if success:
            self.message_user(request, f"Synced {obj.symbol} successfully.", messages.SUCCESS)
        else:
            self.message_user(request, f"Added {obj.symbol} as custom.", messages.WARNING)


# ------------------------------
# Detail Admins
# ------------------------------
@admin.register(StockDetail)
class StockDetailAdmin(admin.ModelAdmin):
    list_display = ("asset", "get_exchange", "get_price", "get_sector", "get_industry", "is_custom")
    search_fields = ("asset__symbol", "asset__name")
    list_filter = ("is_custom", "exchange", "sector")

    def get_exchange(self, obj):
        # If exchange lives in detail, fallback to None if not set
        return getattr(obj, "exchange", None) or getattr(obj.asset, "exchange", None)
    get_exchange.short_description = "Exchange"

    def get_price(self, obj):
        return getattr(obj, "price", None) or getattr(obj.asset, "price", None)
    get_price.short_description = "Price"

    def get_sector(self, obj):
        return getattr(obj, "sector", None) or getattr(obj.asset, "sector", None)
    get_sector.short_description = "Sector"

    def get_industry(self, obj):
        return getattr(obj, "industry", None) or getattr(obj.asset, "industry", None)
    get_industry.short_description = "Industry"


@admin.register(CryptoDetail)
class CryptoDetailAdmin(admin.ModelAdmin):
    list_display = ("asset", "get_price", "get_market_cap", "is_custom")
    search_fields = ("asset__symbol", "asset__name")
    list_filter = ("is_custom",)

    def get_price(self, obj):
        return getattr(obj, "price", None) or getattr(obj.asset, "price", None)
    get_price.short_description = "Price"

    def get_market_cap(self, obj):
        return getattr(obj, "market_cap", None) or getattr(obj.asset, "market_cap", None)
    get_market_cap.short_description = "Market Cap"


@admin.register(MetalDetail)
class MetalDetailAdmin(admin.ModelAdmin):
    list_display = ("asset", "get_price", "get_currency", "is_custom")
    search_fields = ("asset__symbol", "asset__name")
    list_filter = ("is_custom", "currency")

    def get_price(self, obj):
        return getattr(obj, "price", None) or getattr(obj.asset, "price", None)
    get_price.short_description = "Price"

    def get_currency(self, obj):
        return getattr(obj, "currency", None) or getattr(obj.asset, "currency", None)
    get_currency.short_description = "Currency"