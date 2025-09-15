import logging
from django.db import transaction
from assets.models.asset import Asset
from assets.models.details.equity_detail import EquityDetail
from core.types import DomainType
from external_data.fmp.equity import (
    fetch_equity_profile,
    fetch_equity_quote,
    fetch_equity_profiles_bulk,
    fetch_equity_quotes_bulk,
)
from external_data.fmp.isin import fetch_by_isin

logger = logging.getLogger(__name__)


class EquitySyncService:
    @staticmethod
    def sync(asset: Asset) -> bool:
        """
        Sync a single equity asset (profile + quote).
        Falls back to ISIN reconciliation if symbol is invalid.
        """
        if asset.asset_type != DomainType.EQUITY:
            logger.warning(f"Asset {asset} is not EQUITY, skipping")
            return False

        # Ensure detail exists
        detail, _ = EquityDetail.objects.get_or_create(asset=asset)

        # ------------------------------
        # Step 1: Fetch profile
        # ------------------------------
        profile = fetch_equity_profile(asset.symbol)
        if not profile and detail.isin:
            logger.info(
                f"Profile missing for {asset.symbol}, trying ISIN {detail.isin}")
            isin_data = fetch_by_isin(detail.isin)

            if isin_data and isin_data.get("symbol"):
                new_symbol = isin_data["symbol"]
                logger.info(
                    f"Reconciled {asset.symbol} → {new_symbol} using ISIN")

                # Update asset symbol + name
                asset.symbol = new_symbol
                if isin_data.get("companyName"):
                    asset.name = isin_data["companyName"]
                asset.save(update_fields=["symbol", "name"])

                # Retry fetch with new symbol
                profile = fetch_equity_profile(new_symbol)

        if not profile:
            logger.warning(f"No profile data for {asset.symbol}")
            return False

        # ------------------------------
        # Step 2: Fetch quote
        # ------------------------------
        quote = fetch_equity_quote(asset.symbol) or {}

        # ------------------------------
        # Step 3: Merge + Save
        # ------------------------------
        try:
            merged = {**profile, **quote}
            for field, value in merged.items():
                if hasattr(detail, field):
                    setattr(detail, field, value)

            detail.is_custom = False
            detail.save()
            logger.info(f"✅ Synced equity {asset.symbol}")
            return True
        except Exception as e:
            logger.error(
                f"Failed to sync equity {asset.symbol}: {e}", exc_info=True)
            return False

    # ------------------------------
    # Bulk Methods
    # ------------------------------
    @staticmethod
    def sync_profiles_bulk(symbols: list[str]) -> int:
        """
        Bulk sync profiles for multiple symbols.
        Returns count of successfully updated.
        """
        profiles = fetch_equity_profiles_bulk(symbols)
        count = 0
        with transaction.atomic():
            for p in profiles:
                sym = p.get("symbol")
                try:
                    asset = Asset.objects.get(
                        symbol=sym, asset_type=DomainType.EQUITY)
                    detail, _ = EquityDetail.objects.get_or_create(asset=asset)
                    for field, value in p.items():
                        if hasattr(detail, field):
                            setattr(detail, field, value)
                    detail.save()
                    count += 1
                except Asset.DoesNotExist:
                    logger.warning(
                        f"Profile returned for unknown symbol {sym}")
        return count

    @staticmethod
    def sync_quotes_bulk(symbols: list[str]) -> int:
        """
        Bulk sync quotes for multiple symbols.
        Returns count of successfully updated.
        """
        quotes = fetch_equity_quotes_bulk(symbols)
        count = 0
        with transaction.atomic():
            for q in quotes:
                sym = q.get("symbol")
                try:
                    asset = Asset.objects.get(
                        symbol=sym, asset_type=DomainType.EQUITY)
                    detail, _ = EquityDetail.objects.get_or_create(asset=asset)
                    for field, value in q.items():
                        if hasattr(detail, field):
                            setattr(detail, field, value)
                    detail.save(update_fields=list(q.keys()))
                    count += 1
                except Asset.DoesNotExist:
                    logger.warning(f"Quote returned for unknown symbol {sym}")
        return count
