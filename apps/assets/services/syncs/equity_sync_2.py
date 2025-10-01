from assets.models.assets import Asset, AssetIdentifier
from assets.models.details.equity_detail import EquityDetail
from core.types import DomainType
from external_data.fmp.equities.fetchers import (
    fetch_equity_profile, fetch_equity_by_isin, fetch_equity_by_cusip, fetch_equity_by_cik,
    fetch_equity_quote
)
import logging

logger = logging.getLogger(__name__)


class EquitySyncService:
    # -----------
    # HELPER FUNCTIONS
    # -----------
    def _get_primary_ticker(asset: Asset) -> str | None:
        primary = asset.identifiers.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER, is_primary=True
        ).first()
        return primary.value if primary else None

    def _resolve_identifier(asset: Asset) -> tuple[str, str] | None:
        """
        Return the best identifier available for this asset.
        Priority order: TICKER → ISIN → CUSIP → CIK
        """
        priority = [
            AssetIdentifier.IdentifierType.ISIN,
            AssetIdentifier.IdentifierType.CUSIP,
            AssetIdentifier.IdentifierType.CIK,
        ]
        for id_type in priority:
            identifier = asset.identifiers.filter(id_type=id_type).first()
            if identifier:
                return id_type, identifier.value
        return None

    def _search_by_identifier(id_type: str, value: str) -> dict | None:
        """
        Look up an equity profile by a non-ticker identifier (ISIN, CUSIP, CIK, FIGI).
        Returns a normalized profile dict or None.
        """
        if not value:
            return None

        try:
            if id_type == AssetIdentifier.IdentifierType.ISIN:
                return fetch_equity_by_isin(value)

            elif id_type == AssetIdentifier.IdentifierType.CUSIP:
                return fetch_equity_by_cusip(value)

            elif id_type == AssetIdentifier.IdentifierType.CIK:
                return fetch_equity_by_cik(value)

            elif id_type == AssetIdentifier.IdentifierType.FIGI:
                # Not supported by FMP — would require OpenFIGI
                logger.info(f"FIGI lookup not implemented: {value}")
                return None

            else:
                logger.warning(
                    f"Unsupported identifier type in search: {id_type}")
                return None

        except Exception as e:
            logger.error(
                f"Identifier lookup failed ({id_type}: {value}): {e}",
                exc_info=True
            )
            return None

    @staticmethod
    def _get_or_create_detail(asset: Asset) -> EquityDetail:
        detail, _ = EquityDetail.objects.get_or_create(asset=asset)
        return detail

    @staticmethod
    def _update_ticker_identifier(asset: Asset, new_symbol: str) -> None:
        """
        Promote new_symbol as the primary ticker for the asset.
        Demotes any old primary ticker if different.
        """
        new_symbol = new_symbol.upper().strip()

        # Demote old primary ticker if it differs
        old_identifier = asset.identifiers.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER,
            is_primary=True,
        ).first()

        if old_identifier and old_identifier.value != new_symbol:
            old_identifier.is_primary = False
            old_identifier.save()

        # Promote or create new ticker identifier
        new_identifier, _ = AssetIdentifier.objects.get_or_create(
            asset=asset,
            id_type=AssetIdentifier.IdentifierType.TICKER,
            value=new_symbol,
        )
        if not new_identifier.is_primary:
            new_identifier.is_primary = True
            new_identifier.save()

    # -----------
    # SINGLE ASSET
    # -----------

    @staticmethod
    def sync(asset: Asset) -> bool:
        return (
            EquitySyncService.sync_profile(asset)
            and EquitySyncService.sync_quote(asset)
        )

    @staticmethod
    def sync_profile(asset: Asset) -> bool:
        """
        Sync fundamental/company profile for a single equity.
        Uses the primary ticker first. If ticker fails,
        falls back to ISIN → CUSIP → CIK via _search_by_identifier.
        Updates identifiers if a new ticker is discovered.
        """
        if asset.asset_type != DomainType.EQUITY:
            return False

        profile = None

        # --- Try primary ticker first ---
        ticker = EquitySyncService._get_primary_ticker(asset)
        if ticker:
            profile = fetch_equity_profile(ticker)

        # --- Fallback identifiers ---
        if not profile:
            resolved = EquitySyncService._resolve_identifier(asset)
            if resolved:
                id_type, value = resolved
                profile = EquitySyncService._search_by_identifier(
                    id_type, value)

                # If profile reveals a new ticker, update identifiers
                if profile and profile.get("symbol"):
                    EquitySyncService._update_ticker_identifier(
                        asset, profile["symbol"])

        # --- Ensure detail exists ---
        detail, _ = EquityDetail.objects.get_or_create(asset=asset)

        if not profile:
            logger.warning(f"No profile found for {asset}")
            if not asset.is_custom:
                detail.listing_status = "DELISTED"
                detail.save()
            return False

        # --- Apply profile fields ---
        for field, value in profile.items():
            if hasattr(detail, field):
                setattr(detail, field, value)

        if detail.listing_status == "PENDING":
            detail.listing_status = "ACTIVE"

        detail.save()
        return True

    @staticmethod
    def sync_quote(asset: Asset) -> bool:
        """
        Sync market quote for a single equity.
        - Tries primary ticker first.
        - If fails, falls back to ISIN → CUSIP → CIK.
        - Uses identifier-based profile to discover updated ticker.
        - Updates identifiers and retries quote with the new ticker.
        """
        if asset.asset_type != DomainType.EQUITY:
            return False

        detail, _ = EquityDetail.objects.get_or_create(asset=asset)

        # --- Step 1: Try current ticker ---
        ticker = EquitySyncService._get_primary_ticker(asset)
        if ticker:
            quote = fetch_equity_quote(ticker)
            if quote:
                for field, value in quote.items():
                    if hasattr(detail, field):
                        setattr(detail, field, value)
                detail.listing_status = "ACTIVE"
                detail.save()
                return True

        # --- Step 2: Fallback identifiers to resolve new ticker ---
        resolved = EquitySyncService._resolve_identifier(asset)
        if resolved:
            id_type, value = resolved
            profile = EquitySyncService._search_by_identifier(id_type, value)

            if profile and profile.get("symbol"):
                new_symbol = profile["symbol"]
                EquitySyncService._update_ticker_identifier(asset, new_symbol)

                # Retry with updated ticker
                quote = fetch_equity_quote(new_symbol)
                if quote:
                    for field, value in quote.items():
                        if hasattr(detail, field):
                            setattr(detail, field, value)
                    detail.listing_status = "ACTIVE"
                    detail.save()
                    return True

        # --- Step 3: Give up, mark as delisted ---
        detail.listing_status = "DELISTED"
        detail.save()
        return False
