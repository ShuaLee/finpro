import logging

from django.db import transaction

from assets.models.asset_core import Asset, AssetIdentifier
from external_data.exceptions import (
    ExternalDataEmptyResult,
    ExternalDataError,
)
from external_data.providers.fmp.client import FMP_PROVIDER
from external_data.shared.types import EquityIdentifierBundle
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

    @transaction.atomic
    def _sync(self, asset: Asset) -> dict:
        ticker = self._get_ticker(asset)
        if not ticker:
            return {"success": False, "error": "missing_ticker"}

        try:
            identity = FMP_PROVIDER.get_equity_identity(ticker)
        except ExternalDataEmptyResult:
            logger.warning(
                "[IDENTIFIER_SYNC] Ticker not found in provider: %s",
                ticker,
            )
            return {"success": False, "error": "ticker_not_found"}
        except ExternalDataError:
            raise

        self._apply_identifiers(asset, identity.identifiers)

        return {"success": True}

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def _get_ticker(self, asset: Asset) -> str | None:
        ident = asset.identifiers.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER
        ).first()
        return ident.value.upper() if ident else None

    def _apply_identifiers(
            self,
            asset: Asset,
            identifiers: EquityIdentifierBundle,
    ) -> None:
        """
        Persist non-ticker identifiers.
        Ticker already exists and is immutable.
        """
        self._ensure(asset, AssetIdentifier.IdentifierType.ISIN,
                     identifiers.isin)
        self._ensure(asset, AssetIdentifier.IdentifierType.CUSIP,
                     identifiers.cusip)
        self._ensure(asset, AssetIdentifier.IdentifierType.CIK,
                     identifiers.cik)

    def _ensure(
        self,
        asset: Asset,
        id_type: AssetIdentifier.IdentifierType,
        value: str | None,
    ) -> None:
        if not value:
            return

        AssetIdentifier.objects.get_or_create(
            asset=asset,
            id_type=id_type,
            value=value,
        )
