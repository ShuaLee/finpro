import logging
from collections import defaultdict
from django.db import transaction

from assets.models.asset import Asset
from assets.models.details.metal_detail import MetalDetail
from core.types import DomainType
from external_data.fmp.metals.fetchers import (
    fetch_metal_quote,
    bulk_fetch_metal_quotes,
)

logger = logging.getLogger(__name__)


class MetalSyncService:
    @staticmethod
    def sync(asset: Asset) -> bool:
        return MetalSyncService.sync_quote(asset)

    @staticmethod
    def sync_profile(asset: Asset) -> bool:
        # Metals don’t have profiles; treat as always valid
        return True

    @staticmethod
    def sync_quote(asset: Asset) -> bool:
        if asset.asset_type != DomainType.METAL:
            return False

        quote = fetch_metal_quote(asset.symbol)
        if not quote:
            return False

        detail, _ = MetalDetail.objects.get_or_create(asset=asset)
        for field, value in quote.items():
            setattr(detail, field, value)
        detail.is_custom = False
        detail.save()
        return True

    # --- Bulk ---
    @staticmethod
    def sync_profiles_bulk(assets: list[Asset]) -> dict:
        """Metals don’t have real profiles; always success."""
        return {"success": len(assets), "fail": 0}

    @staticmethod
    def sync_quotes_bulk(assets: list[Asset]) -> dict:
        symbols = [a.symbol for a in assets if a.symbol]
        data = bulk_fetch_metal_quotes(symbols)
        results = defaultdict(int)

        with transaction.atomic():
            for asset in assets:
                detail, _ = MetalDetail.objects.get_or_create(asset=asset)
                quote = data.get(asset.symbol)
                if not quote:
                    results["fail"] += 1
                    continue
                for field, value in quote.items():
                    setattr(detail, field, value)
                detail.save()
                results["success"] += 1

        return dict(results)
