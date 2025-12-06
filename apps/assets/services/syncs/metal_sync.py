import logging
from collections import defaultdict
from django.db import transaction

from assets.models.assets import Asset
from assets.models.details.metal_detail import MetalDetail
from external_data.fmp.metals.fetchers import (
    fetch_metal_quote,
    bulk_fetch_metal_quotes,
)

logger = logging.getLogger(__name__)


class MetalSyncService:

    # ----------------------------------------
    # Helpers
    # ----------------------------------------
    @staticmethod
    def _get_symbol(asset: Asset) -> str | None:
        """
        Metals should use their primary identifier as 'symbol'.
        """
        pid = asset.identifiers.filter(is_primary=True).first()
        return pid.value if pid else None

    # ----------------------------------------
    # Sync (single)
    # ----------------------------------------
    @staticmethod
    def sync(asset: Asset) -> bool:
        return MetalSyncService.sync_quote(asset)

    @staticmethod
    def sync_profile(asset: Asset) -> bool:
        # Metals have no profile
        return True

    @staticmethod
    def sync_quote(asset: Asset) -> bool:
        # ✅ Updated domain check (string, not DomainType)
        if asset.asset_type.domain != "METAL":
            return False

        symbol = MetalSyncService._get_symbol(asset)
        if not symbol:
            logger.warning(f"Metal asset {asset} has no primary identifier.")
            return False

        quote = fetch_metal_quote(symbol)
        if not quote:
            return False

        detail, _ = MetalDetail.objects.get_or_create(asset=asset)

        for field, value in quote.items():
            if hasattr(detail, field):
                setattr(detail, field, value)

        detail.is_custom = False
        detail.save()
        return True

    # ----------------------------------------
    # Bulk
    # ----------------------------------------
    @staticmethod
    def sync_profiles_bulk(assets: list[Asset]) -> dict:
        """
        Metals have no profiles — count only metal assets and return success.
        """
        count = sum(1 for a in assets if a.asset_type.domain == "METAL")
        return {"success": count, "fail": 0}

    @staticmethod
    def sync_quotes_bulk(assets: list[Asset]) -> dict:
        results = defaultdict(int)

        # Build {asset: symbol}
        symbols = {
            asset: MetalSyncService._get_symbol(asset)
            for asset in assets
            if asset.asset_type.domain == "METAL"
        }
        symbols = {a: s for a, s in symbols.items() if s}

        if not symbols:
            return {"success": 0, "fail": len(assets)}

        # Fetch all metal quotes in bulk
        data = bulk_fetch_metal_quotes(list(symbols.values()))

        with transaction.atomic():
            for asset, symbol in symbols.items():
                quote = data.get(symbol)
                if not quote:
                    results["fail"] += 1
                    continue

                detail, _ = MetalDetail.objects.get_or_create(asset=asset)

                for field, value in quote.items():
                    if hasattr(detail, field):
                        setattr(detail, field, value)

                detail.save()
                results["success"] += 1

        return dict(results)
