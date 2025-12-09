import logging
from collections import defaultdict
from django.db import transaction

from apps.assets.models.asset_core.asset import Asset
from assets.models.details.bond_detail import BondDetail

from external_data.fmp.bonds.fetchers import (
    fetch_bond_profile,
    fetch_bond_quote,
    bulk_fetch_bond_quotes,
)
from external_data.fmp.shared.isin import search_by_isin

logger = logging.getLogger(__name__)


# --------------------------------------------
# Helpers
# --------------------------------------------
def _get_bond_symbol(asset: Asset) -> str | None:
    """
    Returns the primary identifier value for bond sync lookups.
    Bonds typically use CUSIP or ISIN.
    """
    pid = asset.primary_identifier
    return pid.value if pid else None


# --------------------------------------------
# Bond Sync
# --------------------------------------------
class BondSyncService:

    @staticmethod
    def sync(asset: Asset) -> bool:
        return (
            BondSyncService.sync_profile(asset)
            and BondSyncService.sync_quote(asset)
        )

    # -------------------------------------------------------------
    # Sync Profile
    # -------------------------------------------------------------
    @staticmethod
    def sync_profile(asset: Asset) -> bool:

        if asset.asset_type.slug != "bond":
            return False

        symbol = _get_bond_symbol(asset)
        if not symbol:
            logger.warning(f"Bond {asset.id} has no identifier")
            return False

        profile = fetch_bond_profile(symbol)

        # Fallback: search by ISIN
        if not profile:
            detail = getattr(asset, "bond_detail", None)
            if detail and detail.isin:
                profile = search_by_isin(detail.isin)

        if not profile:
            logger.warning(f"No profile found for bond {symbol}")
            return False

        detail, _ = BondDetail.objects.get_or_create(asset=asset)

        for field, value in profile.items():
            if hasattr(detail, field):
                setattr(detail, field, value)

        detail.is_custom = False
        detail.save()
        return True

    # -------------------------------------------------------------
    # Sync Quote
    # -------------------------------------------------------------
    @staticmethod
    def sync_quote(asset: Asset) -> bool:

        if asset.asset_type.slug != "bond":
            return False

        symbol = _get_bond_symbol(asset)
        if not symbol:
            logger.warning(f"Bond {asset.id} has no identifier")
            return False

        quote = fetch_bond_quote(symbol)
        if not quote:
            logger.warning(f"No quote found for bond {symbol}")
            return False

        detail, _ = BondDetail.objects.get_or_create(asset=asset)

        for field, value in quote.items():
            if hasattr(detail, field):
                setattr(detail, field, value)

        detail.save()
        return True

    # -------------------------------------------------------------
    # Bulk profile sync (no bulk API for profiles)
    # -------------------------------------------------------------
    @staticmethod
    def sync_profiles_bulk(assets: list[Asset]) -> dict:
        results = defaultdict(int)

        with transaction.atomic():
            for asset in assets:
                if BondSyncService.sync_profile(asset):
                    results["success"] += 1
                else:
                    results["fail"] += 1

        return dict(results)

    # -------------------------------------------------------------
    # Bulk quote sync (supported via FMP)
    # -------------------------------------------------------------
    @staticmethod
    def sync_quotes_bulk(assets: list[Asset]) -> dict:
        results = defaultdict(int)

        symbol_map = {
            asset: _get_bond_symbol(asset)
            for asset in assets
            if _get_bond_symbol(asset)
        }

        symbols = list(symbol_map.values())

        quotes = bulk_fetch_bond_quotes(symbols)

        with transaction.atomic():
            for asset, symbol in symbol_map.items():

                detail, _ = BondDetail.objects.get_or_create(asset=asset)

                quote = quotes.get(symbol)
                if not quote:
                    results["fail"] += 1
                    continue

                for field, value in quote.items():
                    if hasattr(detail, field):
                        setattr(detail, field, value)

                detail.save()
                results["success"] += 1

        return dict(results)
