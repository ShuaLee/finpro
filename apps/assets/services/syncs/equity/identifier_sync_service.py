import logging

from django.db import transaction

from assets.models.asset_core import Asset, AssetIdentifier
from assets.services.utils import get_primary_ticker
from external_data.fmp.equities.fetchers import (
    fetch_equity_profile,
    fetch_equity_by_isin,
    fetch_equity_by_cik,
    fetch_equity_by_cusip,
)

logger = logging.getLogger(__name__)


class EquityIdentifierSyncService:
    EXPECTED_TYPES = [
        AssetIdentifier.IdentifierType.TICKER,
        AssetIdentifier.IdentifierType.ISIN,
        AssetIdentifier.IdentifierType.CUSIP,
        AssetIdentifier.IdentifierType.CIK,
    ]

    # ============================================================
    # Entry
    # ============================================================
    @transaction.atomic
    def sync(self, asset: Asset) -> dict:
        if asset.asset_type.slug != "equity":
            return {"success": False, "error": "non_equity_asset"}

        ticker = get_primary_ticker(asset)

        if ticker:
            return self._sync_using_ticker(asset, ticker)

        return self._sync_using_secondary_ids(asset)

    # ============================================================
    # Primary path: lookup via ticker
    # ============================================================
    def _sync_using_ticker(self, asset: Asset, ticker: str) -> dict:
        profile = fetch_equity_profile(ticker)

        # Garbage ticker or partial response → fallback
        if (
            not profile
            or "identifiers" not in profile
            or not profile["identifiers"].get("TICKER")
        ):
            return self._sync_using_secondary_ids(asset)

        identifiers = profile["identifiers"]
        result = {t: "missing" for t in self.EXPECTED_TYPES}

        # ---- Ticker ----
        new_ticker = identifiers["TICKER"].upper()
        if new_ticker != ticker.upper():
            self._set_primary_ticker(asset, new_ticker)
            result[AssetIdentifier.IdentifierType.TICKER] = "updated"
        else:
            result[AssetIdentifier.IdentifierType.TICKER] = "unchanged"

        # ---- Other identifiers ----
        for id_type in (
            AssetIdentifier.IdentifierType.ISIN,
            AssetIdentifier.IdentifierType.CUSIP,
            AssetIdentifier.IdentifierType.CIK,
        ):
            value = identifiers.get(id_type)
            if not value:
                continue

            value = str(value).upper()

            ident, created = AssetIdentifier.objects.get_or_create(
                asset=asset,
                id_type=id_type,
                value=value,
            )

            result[id_type] = "added" if created else "unchanged"

        result["success"] = True
        return result

    # ============================================================
    # Secondary path: lookup via ISIN / CUSIP / CIK
    # ============================================================
    def _sync_using_secondary_ids(self, asset: Asset) -> dict:
        result = {t: "missing" for t in self.EXPECTED_TYPES}

        id_type, value = self._resolve_available_identifier(asset)
        if not value:
            return {"success": False, "error": "no_identifiers_available"}

        lookup = {
            AssetIdentifier.IdentifierType.ISIN: fetch_equity_by_isin,
            AssetIdentifier.IdentifierType.CUSIP: fetch_equity_by_cusip,
            AssetIdentifier.IdentifierType.CIK: fetch_equity_by_cik,
        }.get(id_type)

        response = lookup(value)
        if not response or not response.get("symbol"):
            return {"success": False, "error": "lookup_failed"}

        # Found correct ticker
        ticker = response["symbol"].upper()
        self._set_primary_ticker(asset, ticker)
        result[AssetIdentifier.IdentifierType.TICKER] = "updated"

        # Other identifiers
        identifiers = response.get("identifiers", {})
        for id_type in (
            AssetIdentifier.IdentifierType.ISIN,
            AssetIdentifier.IdentifierType.CUSIP,
            AssetIdentifier.IdentifierType.CIK,
        ):
            value = identifiers.get(id_type)
            if not value:
                continue

            value = str(value).upper()
            _, created = AssetIdentifier.objects.get_or_create(
                asset=asset,
                id_type=id_type,
                value=value,
            )
            result[id_type] = "added" if created else "unchanged"

        result["success"] = True
        return result

    # ============================================================
    # Helpers
    # ============================================================
    def _resolve_available_identifier(self, asset: Asset):
        for id_type in (
            AssetIdentifier.IdentifierType.ISIN,
            AssetIdentifier.IdentifierType.CUSIP,
            AssetIdentifier.IdentifierType.CIK,
        ):
            ident = asset.identifiers.filter(id_type=id_type).first()
            if ident:
                return id_type, ident.value
        return None, None

    def _set_primary_ticker(self, asset: Asset, ticker: str):
        """
        Sets the primary ticker and removes all other tickers.
        """
        ticker = ticker.upper()

        # 1️⃣ Demote any existing primary ticker
        asset.identifiers.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER,
            is_primary=True,
        ).exclude(value=ticker).update(is_primary=False)

        # 2️⃣ Promote or create the new primary ticker
        ident, _ = AssetIdentifier.objects.get_or_create(
            asset=asset,
            id_type=AssetIdentifier.IdentifierType.TICKER,
            value=ticker,
        )

        if not ident.is_primary:
            ident.is_primary = True
            ident.save(update_fields=["is_primary"])

        # 3️⃣ Delete ALL non-primary tickers (safe now)
        asset.identifiers.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER,
            is_primary=False,
        ).exclude(value=ticker).delete()
