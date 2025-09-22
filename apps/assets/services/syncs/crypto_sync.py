import logging
from collections import defaultdict
from django.db import transaction

from assets.models.assets import Asset
from assets.models.details.crypto_detail import CryptoDetail
from core.types import DomainType
from external_data.fmp.crypto.fetchers import (
    fetch_crypto_profile,
    fetch_crypto_quote,
    bulk_fetch_crypto_quotes,
)

logger = logging.getLogger(__name__)


class CryptoSyncService:
    @staticmethod
    def sync(asset: Asset) -> bool:
        return (
            CryptoSyncService.sync_profile(asset)
            and CryptoSyncService.sync_quote(asset)
        )

    @staticmethod
    def sync_profile(asset: Asset) -> bool:
        if asset.asset_type != DomainType.CRYPTO:
            return False

        profile = fetch_crypto_profile(asset.symbol)
        if not profile:
            return False

        detail, _ = CryptoDetail.objects.get_or_create(asset=asset)
        for field, value in profile.items():
            setattr(detail, field, value)
        detail.is_custom = False
        detail.save()
        return True

    @staticmethod
    def sync_quote(asset: Asset) -> bool:
        if asset.asset_type != DomainType.CRYPTO:
            return False

        quote = fetch_crypto_quote(asset.symbol)
        if not quote:
            return False

        detail, _ = CryptoDetail.objects.get_or_create(asset=asset)
        for field, value in quote.items():
            setattr(detail, field, value)
        detail.save()
        return True

    # --- Bulk ---
    @staticmethod
    def sync_profiles_bulk(assets: list[Asset]) -> dict:
        """Profiles must be looped (no bulk API)."""
        results = defaultdict(int)
        with transaction.atomic():
            for asset in assets:
                if CryptoSyncService.sync_profile(asset):
                    results["success"] += 1
                else:
                    results["fail"] += 1
        return dict(results)

    @staticmethod
    def sync_quotes_bulk(assets: list[Asset]) -> dict:
        """Quotes can be fetched in batch from FMP."""
        symbols = [a.symbol for a in assets if a.symbol]
        data = bulk_fetch_crypto_quotes(symbols)
        results = defaultdict(int)

        with transaction.atomic():
            for asset in assets:
                detail, _ = CryptoDetail.objects.get_or_create(asset=asset)
                quote = data.get(asset.symbol)
                if not quote:
                    results["fail"] += 1
                    continue
                for field, value in quote.items():
                    setattr(detail, field, value)
                detail.save()
                results["success"] += 1

        return dict(results)
