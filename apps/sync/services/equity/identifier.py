import logging

from django.db import transaction

from assets.models.asset_core import Asset, AssetIdentifier
from external_data.exceptions import (
    ExternalDataEmptyResult,
    ExternalDataError,
)
from external_data.providers.fmp.client import FMP_PROVIDER
from external_data.shared.types import IdentifierBundle
from sync.services.base import BaseSyncService

logger = logging.getLogger(__name__)


class EquityIdentifierSyncService(BaseSyncService):
    """
    Syncs equity identifiers (ticker, ISIN, CUSIP, CIK).

    This service is responsible for:
    - Proving the symbol exists
    - Detecting renamed tickers
    - Hydrating identifiers
    - Updating the primary ticker when required

    This service MUST run before all other equity syncs.
    """

    name = "equity.identifiers"

    # ==================================================
    # Public sync entry
    # ==================================================
    @transaction.atomic
    def _sync(self, asset: Asset) -> dict:

        primary_ticker = self._get_primary_ticker(asset)
        if not primary_ticker:
            return {"success": False, "error": "missing_primary_ticker"}

        provider = FMP_PROVIDER

        try:
            identity = provider.get_equity_identity(primary_ticker)
        except ExternalDataEmptyResult:
            # Symbol does not exist -> attempt rename resolution
            return self._handle_possible_rename(asset, primary_ticker, provider)
        except ExternalDataError:
            # Provider failure / invalid response -> propagate
            raise

        # Symbol is valid -> hydrate identifiers
        self._apply_identifiers(asset, identity.identifiers)

        return {"success": True}

    # ==================================================
    # Rename handling
    # ==================================================
    def _handle_possible_rename(self, asset: Asset, old_symbol: str, provider) -> dict:
        """
        Attempt to resolve renamed / changed symbols.
        """
        candidates = provider.resolve_symbol(old_symbol)

        if not candidates:
            logger.warning(
                "[IDENTIFIER_SYNC] No rename candidates found for %s",
                old_symbol,
            )
            return {"success": False, "error": "symbol_not_found"}

        # Take the strongest candidate (provider orders relevance)
        candidate = candidates[0]
        new_symbol = candidate.symbol.upper()

        logger.info(
            "[IDENTIFIER_SYNC] Symbol rename detected: %s → %s",
            old_symbol,
            new_symbol,
        )

        # Update primary ticker
        self._set_primary_ticker(asset, new_symbol)

        # Re-fetch identity using new symbol
        identity = provider.get_equity_identity(new_symbol)

        self._apply_identifiers(asset, identity.identifiers)

        return {
            "success": True,
            "renamed": True,
            "old_symbol": old_symbol,
            "new_symbol": new_symbol,
        }

    # ==================================================
    # Identifier application
    # ==================================================
    def _apply_identifiers(
        self,
        asset: Asset,
        identifiers: IdentifierBundle,
    ) -> None:
        """
        Persist identifier bundle to the database.
        """
        if identifiers.ticker:
            self._ensure_identifier(
                asset,
                AssetIdentifier.IdentifierType.TICKER,
                identifiers.ticker,
                primary=True,
            )

        if identifiers.isin:
            self._ensure_identifier(
                asset,
                AssetIdentifier.IdentifierType.ISIN,
                identifiers.isin,
            )

        if identifiers.cusip:
            self._ensure_identifier(
                asset,
                AssetIdentifier.IdentifierType.CUSIP,
                identifiers.cusip,
            )

        if identifiers.cik:
            self._ensure_identifier(
                asset,
                AssetIdentifier.IdentifierType.CIK,
                identifiers.cik,
            )

    def _ensure_identifier(
        self,
        asset: Asset,
        id_type: AssetIdentifier.IdentifierType,
        value: str,
        *,
        primary: bool = False,
    ) -> None:
        """
        Create identifier if missing. Never deletes identifiers.
        """
        ident, created = AssetIdentifier.objects.get_or_create(
            asset=asset,
            id_type=id_type,
            value=value,
            defaults={"is_primary": primary},
        )

        if primary and not ident.is_primary:
            ident.is_primary = True
            ident.save(update_fields=["is_primary"])

    # ==================================================
    # Primary ticker helpers
    # ==================================================
    def _get_primary_ticker(self, asset: Asset) -> str | None:
        ident = asset.identifiers.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER,
            is_primary=True,
        ).first()
        return ident.value.upper() if ident else None

    def _set_primary_ticker(self, asset: Asset, symbol: str) -> None:
        """
        Demotes old primary ticker and promotes new one.
        """
        asset.identifiers.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER,
            is_primary=True,
        ).update(is_primary=False)

        AssetIdentifier.objects.update_or_create(
            asset=asset,
            id_type=AssetIdentifier.IdentifierType.TICKER,
            value=symbol,
            defaults={"is_primary": True},
        )
