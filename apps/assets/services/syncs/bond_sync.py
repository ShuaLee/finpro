import logging
from collections import defaultdict
from django.db import transaction

from assets.models.asset import Asset
from assets.models.details.bond_detail import BondDetail
from core.types import DomainType
from external_data.fmp.bonds.fetchers import (
    fetch_bond_profile,
    fetch_bond_quote,
    bulk_fetch_bond_quotes,
)
from external_data.fmp.shared.isin import search_by_isin

logger = logging.getLogger(__name__)


class BondSyncService:
    @staticmethod
    def sync(asset: Asset) -> bool:
        return (
            BondSyncService.sync_profile(asset)
            and BondSyncService.sync_quote(asset)
        )

    @staticmethod
    def sync_profile(asset: Asset) -> bool:
        if asset.asset_type != DomainType.BOND:
            return False

        profile = fetch_bond_profile(asset.symbol)
        if not profile:
            detail = getattr(asset, "bond_detail", None)
            if detail and detail.isin:
                profile = search_by_isin(detail.isin)

        if not profile:
            logger.warning(f"No profile for bond {asset.symbol}")
            return False

        detail, _ = BondDetail.objects.get_or_create(asset=asset)
        for field, value in profile.items():
            setattr(detail, field, value)
        detail.is_custom = False
        detail.save()
        return True

    @staticmethod
    def sync_quote(asset: Asset) -> bool:
        if asset.asset_type != DomainType.BOND:
            return False

        quote = fetch_bond_quote(asset.symbol)
        if not quote:
            logger.warning(f"No quote for bond {asset.symbol}")
            return False

        detail, _ = BondDetail.objects.get_or_create(asset=asset)
        for field, value in quote.items():
            setattr(detail, field, value)
        detail.save()
        return True

    # --- Bulk ---
    @staticmethod
    def sync_profiles_bulk(assets: list[Asset]) -> dict:
        """
        No bulk API for bond profiles → loop through single fetches.
        """
        results = defaultdict(int)
        with transaction.atomic():
            for asset in assets:
                if BondSyncService.sync_profile(asset):
                    results["success"] += 1
                else:
                    results["fail"] += 1
        return dict(results)

    @staticmethod
    def sync_quotes_bulk(assets: list[Asset]) -> dict:
        """
        Bulk quotes available → use batch fetch.
        """
        results = defaultdict(int)
        symbols = [a.symbol for a in assets if a.symbol]
        quotes = bulk_fetch_bond_quotes(symbols)

        with transaction.atomic():
            for asset in assets:
                detail, _ = BondDetail.objects.get_or_create(asset=asset)
                quote = quotes.get(asset.symbol)
                if not quote:
                    results["fail"] += 1
                    continue
                for field, value in quote.items():
                    setattr(detail, field, value)
                detail.save()
                results["success"] += 1

        return dict(results)
