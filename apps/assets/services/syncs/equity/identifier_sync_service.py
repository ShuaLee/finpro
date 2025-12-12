import logging

from django.db import transaction

from assets.models.asset_core import Asset, AssetIdentifier
from assets.services.utils import get_primary_ticker, hydrate_identifiers
from external_data.fmp.equities.fetchers import (
    fetch_equity_profile,
    fetch_equity_by_isin,
    fetch_equity_by_cik,
    fetch_equity_by_cusip
)

logger = logging.getLogger(__name__)


class EquityIdentifierSyncService:
    """
    Responsible ONLY for:
      - Ensuring ticker is correct
      - Resolving ticker via ISIN/CUSIP/CIK
      - Hydrating ISIN/CUSIP/CIK identifiers from profile response
    """

    # =============================
    # PUBLIC SYNC ENTRYPOINT
    # =============================
    @staticmethod
    @transaction.atomic
    def sync(self, asset: Asset) -> bool:
        if asset.asset_type.slug != "equity":
            return False

        # 1. If asset already has a ticker -> validate it
        ticker = get_primary_ticker(asset)
        if ticker:
            return self._sync_using_ticker(asset, ticker)

        # 2. Otherwise attemp identifier-based lookup
        return self._sync_using_secondary_ids(asset)

    # =============================
    # TICKER LOOKUP
    # =============================
    def _sync_using_ticker(self, asset: Asset, ticker: str) -> bool:
        profile = fetch_equity_profile(ticker)

        if not profile:
            # fallback: try ISIN, CUSIP, CIK
            return self._sync_using_secondary_ids(asset)

        symbol = profile["symbol"].upper()

        # ticker changed?
        if symbol != ticker.upper():
            logger.info(f"[IDENTIFIER] Renaming {ticker} -> {symbol}")
            self._update_primary_ticker(asset, symbol)

        # hydrate identifiers from profile
        hydrate_identifiers(asset, profile["identifiers"])

        return True

    # =============================
    # FALLBACK IDENTIFIER LOOKUPS
    # =============================
    def _sync_using_secondary_ids(self, asset: Asset) -> bool:
        id_type, value = self._resolve_available_identifier(asset)
        if not value:
            return False

        logger.info(f"[IDENTIFIER] Attempting lookup via {id_type}={value}")

        lookup = {
            AssetIdentifier.IdentifierType.ISIN: fetch_equity_by_isin,
            AssetIdentifier.IdentifierType.CUSIP: fetch_equity_by_cusip,
            AssetIdentifier.IdentifierType.CIK: fetch_equity_by_cik,
        }.get(id_type)

        if not lookup:
            return False

        result = lookup(value)
        if not result or not result.get("symbol"):
            return False

        symbol = result["symbol"].upper()
        self._update_primary_ticker(asset, symbol)

        return True

    # =============================
    # INTERNAL HELPERS
    # =============================
    def _resolve_available_identifier(self, asset: Asset):
        for id_type in [
            AssetIdentifier.IdentifierType.ISIN,
            AssetIdentifier.IdentifierType.CUSIP,
            AssetIdentifier.IdentifierType.CIK,
        ]:
            ident = asset.identifiers.filter(id_type=id_type).first()
            if ident:
                return id_type, ident.value
        return None, None

    def _update_primary_ticker(self, asset: Asset, ticker: str):
        ticker = ticker.upper()

        # demote old primary ticker
        old = asset.identifiers.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER,
            is_primary=True,
        ).first()

        if old and old.value != ticker:
            old.is_primary = False
            old.save()

        ident, _ = AssetIdentifier.objects.get_or_create(
            asset=asset,
            id_type=AssetIdentifier.IdentifierType.TICKER,
            value=ticker,
        )

        if not ident.is_primary:
            ident.is_primary = True
            ident.save()
