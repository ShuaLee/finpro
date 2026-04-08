from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.assets.models import Asset, AssetMarketData, AssetType
from apps.assets.services import AssetService
from apps.integrations.models import ActiveCryptoListing


class ActiveCryptoAssetService:
    @staticmethod
    def _get_crypto_type() -> AssetType:
        asset_type = AssetType.objects.filter(
            created_by__isnull=True,
            slug__in=["crypto", "cryptocurrency"],
        ).first()
        if asset_type is None:
            raise ValidationError("System asset type 'Cryptocurrency' is required before tracked crypto can be added.")
        return asset_type

    @staticmethod
    def _get_listing(*, symbol: str) -> ActiveCryptoListing:
        normalized = (symbol or "").strip().upper()
        listing = ActiveCryptoListing.objects.filter(provider="fmp", symbol=normalized).first()
        if listing is None:
            raise ValidationError({"active_crypto_symbol": "That crypto pair is not in the current crypto list."})
        return listing

    @staticmethod
    @transaction.atomic
    def get_or_create_public_asset(*, symbol: str) -> Asset:
        listing = ActiveCryptoAssetService._get_listing(symbol=symbol)
        asset_type = ActiveCryptoAssetService._get_crypto_type()

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
                    "crypto_profile": {
                        "base_symbol": listing.base_symbol,
                        "quote_currency": listing.quote_currency,
                    }
                },
                is_active=True,
            )

        market_data = getattr(asset, "market_data", None)
        if market_data is None:
            market_data = AssetMarketData(asset=asset, provider=AssetMarketData.Provider.FMP)

        now = timezone.now()
        market_data.provider_symbol = listing.symbol
        market_data.last_seen_symbol = listing.symbol
        market_data.last_seen_name = listing.name
        market_data.status = AssetMarketData.Status.TRACKED
        market_data.last_synced_at = now
        market_data.last_successful_sync_at = now
        market_data.last_error = ""
        market_data.save()

        asset.name = listing.name
        asset.symbol = listing.symbol
        asset.is_active = True
        asset.data = {
            **asset.data,
            "crypto_profile": {
                "base_symbol": listing.base_symbol,
                "quote_currency": listing.quote_currency,
            },
        }
        asset.save()
        return asset
