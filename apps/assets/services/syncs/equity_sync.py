import logging
from collections import defaultdict
from django.db import transaction

from assets.models.asset import Asset
from assets.models.details.equity_detail import EquityDetail
from core.types import DomainType
from external_data.fmp.equities.fetchers import (
    fetch_equity_profile,
    fetch_equity_quote,
    fetch_equity_quotes_bulk,
    fetch_equity_profiles_bulk,
)
from external_data.fmp.shared.isin import search_by_isin

logger = logging.getLogger(__name__)


class EquitySyncService:
    @staticmethod
    def sync(asset: Asset) -> bool:
        """Full sync (profile + quote)."""
        profile_ok = EquitySyncService.sync_profile(asset)
        quote_ok = EquitySyncService.sync_quote(asset)
        return profile_ok and quote_ok

    @staticmethod
    def sync_profile(asset: Asset) -> bool:
        if asset.asset_type != DomainType.EQUITY:
            return False

        profile = fetch_equity_profile(asset.symbol)

        # fallback via ISIN
        if not profile:
            detail = getattr(asset, "equity_detail", None)
            if detail and detail.isin:
                profile = search_by_isin(detail.isin)

        detail, _ = EquityDetail.objects.get_or_create(asset=asset)

        if not profile:
            logger.warning(f"No profile for {asset.symbol}")
            detail.listing_status = "DELISTED"
            detail.save()
            return False

        for field, value in profile.items():
            setattr(detail, field, value)

        detail.is_custom = False
        detail.listing_status = "ACTIVE"
        detail.save()
        return True

    @staticmethod
    def sync_quote(asset: Asset) -> bool:
        if asset.asset_type != DomainType.EQUITY:
            return False

        quote = fetch_equity_quote(asset.symbol)
        detail, _ = EquityDetail.objects.get_or_create(asset=asset)

        if not quote:
            logger.warning(f"No quote for {asset.symbol}")
            detail.listing_status = "DELISTED"
            detail.save()
            return False

        for field, value in quote.items():
            setattr(detail, field, value)

        detail.listing_status = "ACTIVE"
        detail.save()
        return True

    # --- Bulk ---
    @staticmethod
    def sync_profiles_bulk() -> dict:
        """
        Bulk sync all equity profiles using FMP bulk profile API.
        Iterates across all 'part' chunks until no more data is returned.
        """
        results = defaultdict(int)
        part = 0

        while True:
            profiles = fetch_equity_profiles_bulk(part)
            if not profiles:
                break  # stop when no more data returned

            with transaction.atomic():
                for record in profiles:
                    symbol = record.get("symbol")
                    if not symbol:
                        continue

                    try:
                        asset = Asset.objects.get(
                            asset_type=DomainType.EQUITY,
                            symbol=symbol
                        )
                    except Asset.DoesNotExist:
                        continue  # skip if symbol not in DB

                    detail, _ = EquityDetail.objects.get_or_create(asset=asset)
                    for field, value in record.items():
                        if hasattr(detail, field):
                            setattr(detail, field, value)
                    detail.is_custom = False
                    detail.save()
                    results["success"] += 1

            part += 1

        return dict(results)

    @staticmethod
    def sync_quotes_bulk(assets: list[Asset]) -> dict:
        """Bulk sync quotes using FMP batch endpoint."""
        symbols = [a.symbol for a in assets if a.symbol]
        data = fetch_equity_quotes_bulk(symbols)
        results = defaultdict(int)

        with transaction.atomic():
            for asset in assets:
                detail, _ = EquityDetail.objects.get_or_create(asset=asset)
                quote = data.get(asset.symbol)
                if not quote:
                    results["fail"] += 1
                    detail.listing_status = "DELISTED"
                    detail.save()
                    continue

                for field, value in quote.items():
                    setattr(detail, field, value)

                detail.listing_status = "ACTIVE"
                detail.save()
                results["success"] += 1

        return dict(results)
