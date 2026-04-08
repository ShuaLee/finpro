from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.assets.models import Asset, AssetPrice
from apps.assets.services.public_asset_sync_service import PublicAssetSyncService
from apps.integrations.exceptions import EmptyProviderResult, IntegrationError


class AssetPriceService:
    @staticmethod
    def cache_ttl() -> timedelta:
        return timedelta(seconds=getattr(settings, "ASSET_PRICE_CACHE_TTL_SECONDS", 600))

    @staticmethod
    def is_price_fresh(*, asset_price: AssetPrice | None, now=None) -> bool:
        if asset_price is None:
            return False
        reference_time = now or timezone.now()
        return asset_price.as_of >= reference_time - AssetPriceService.cache_ttl()

    @staticmethod
    def get_cached_price(*, asset: Asset) -> AssetPrice | None:
        return getattr(asset, "price", None)

    @staticmethod
    def get_current_price(
        *,
        asset: Asset,
        force_refresh: bool = False,
    ) -> AssetPrice:
        cached_price = AssetPriceService.get_cached_price(asset=asset)
        if not force_refresh and AssetPriceService.is_price_fresh(asset_price=cached_price):
            return cached_price
        try:
            return PublicAssetSyncService.refresh_quote(asset=asset)
        except (EmptyProviderResult, IntegrationError):
            if cached_price is not None:
                return cached_price
            raise
