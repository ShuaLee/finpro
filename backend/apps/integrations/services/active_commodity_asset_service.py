from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.assets.models import Asset, AssetMarketData, AssetType
from apps.assets.services import AssetService
from apps.integrations.models import ActiveCommodityListing
from apps.integrations.services.constants import PRECIOUS_METAL_COMMODITY_MAP


class ActiveCommodityAssetService:
    @staticmethod
    def _get_type(*, slug: str, display_name: str) -> AssetType:
        asset_type = AssetType.objects.filter(created_by__isnull=True, slug=slug).first()
        if asset_type is None:
            raise ValidationError(f"System asset type '{display_name}' is required before tracked assets can be added.")
        return asset_type

    @staticmethod
    def _get_listing(*, symbol: str) -> ActiveCommodityListing:
        normalized = (symbol or "").strip().upper()
        listing = ActiveCommodityListing.objects.filter(provider="fmp", symbol=normalized).first()
        if listing is None:
            raise ValidationError({"active_commodity_symbol": "That commodity is not in the current commodity list."})
        return listing

    @staticmethod
    def _upsert_market_data(*, asset: Asset, provider_symbol: str, name: str) -> None:
        market_data = getattr(asset, "market_data", None)
        if market_data is None:
            market_data = AssetMarketData(asset=asset, provider=AssetMarketData.Provider.FMP)

        now = timezone.now()
        market_data.provider_symbol = provider_symbol
        market_data.last_seen_symbol = provider_symbol
        market_data.last_seen_name = name
        market_data.status = AssetMarketData.Status.TRACKED
        market_data.last_synced_at = now
        market_data.last_successful_sync_at = now
        market_data.last_error = ""
        market_data.save()

    @staticmethod
    @transaction.atomic
    def get_or_create_public_asset(*, symbol: str) -> Asset:
        listing = ActiveCommodityAssetService._get_listing(symbol=symbol)
        asset_type = ActiveCommodityAssetService._get_type(slug="commodity", display_name="Commodity")

        asset = (
            Asset.objects.select_related("market_data")
            .filter(owner__isnull=True, asset_type=asset_type, symbol=listing.symbol)
            .first()
        )
        if asset is None:
            asset = AssetService.create_asset(
                asset_type=asset_type,
                owner=None,
                name=listing.name,
                symbol=listing.symbol,
                data={
                    "commodity_profile": {
                        "exchange": listing.exchange,
                        "trade_month": listing.trade_month,
                        "currency": listing.currency,
                    }
                },
                is_active=True,
            )

        ActiveCommodityAssetService._upsert_market_data(
            asset=asset,
            provider_symbol=listing.symbol,
            name=listing.name,
        )
        asset.name = listing.name
        asset.symbol = listing.symbol
        asset.is_active = True
        asset.data = {
            **asset.data,
            "commodity_profile": {
                "exchange": listing.exchange,
                "trade_month": listing.trade_month,
                "currency": listing.currency,
            },
        }
        asset.save()
        return asset

    @staticmethod
    @transaction.atomic
    def get_or_create_precious_metal_asset(*, metal: str) -> Asset:
        normalized = (metal or "").strip().lower()
        metal_spec = PRECIOUS_METAL_COMMODITY_MAP.get(normalized)
        if metal_spec is None:
            raise ValidationError({"precious_metal_code": "Unsupported precious metal code."})

        commodity_listing = ActiveCommodityAssetService._get_listing(symbol=metal_spec["symbol"])
        asset_type = ActiveCommodityAssetService._get_type(
            slug="precious_metal",
            display_name="Precious Metal",
        )
        asset_name = metal_spec["name"]

        asset = (
            Asset.objects.select_related("market_data")
            .filter(
                owner__isnull=True,
                asset_type=asset_type,
                name=asset_name,
                symbol=commodity_listing.symbol,
            )
            .first()
        )
        if asset is None:
            asset = AssetService.create_asset(
                asset_type=asset_type,
                owner=None,
                name=asset_name,
                symbol=commodity_listing.symbol,
                data={
                    "precious_metal_profile": {
                        "metal": normalized,
                        "unit": "ozt",
                        "spot_commodity_symbol": commodity_listing.symbol,
                        "spot_commodity_name": commodity_listing.name,
                    }
                },
                is_active=True,
            )

        ActiveCommodityAssetService._upsert_market_data(
            asset=asset,
            provider_symbol=commodity_listing.symbol,
            name=asset_name,
        )
        asset.name = asset_name
        asset.symbol = commodity_listing.symbol
        asset.is_active = True
        asset.data = {
            **asset.data,
            "precious_metal_profile": {
                "metal": normalized,
                "unit": "ozt",
                "spot_commodity_symbol": commodity_listing.symbol,
                "spot_commodity_name": commodity_listing.name,
            },
        }
        asset.save()
        return asset
