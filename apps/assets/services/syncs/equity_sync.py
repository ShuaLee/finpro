import logging
from collections import defaultdict
from django.db import transaction
from assets.models.assets import Asset, AssetIdentifier
from assets.models.details.equity_detail import EquityDetail
from core.types import DomainType
from external_data.fmp.equities.fetchers import (
    fetch_equity_profile, fetch_equity_quote,
    fetch_equity_profiles_bulk, fetch_equity_quotes_bulk, fetch_equity_universe
)
from external_data.fmp.shared.isin import search_by_isin

logger = logging.getLogger(__name__)


# --- Helpers ---
def _get_primary_ticker(asset: Asset) -> str | None:
    primary = asset.identifiers.filter(
        id_type=AssetIdentifier.IdentifierType.TICKER, is_primary=True
    ).first()
    return primary.value if primary else None


def _apply_fields(model, data: dict):
    for field, value in data.items():
        if hasattr(model, field):
            setattr(model, field, value)


def _upsert_identifier(asset: Asset, id_type, value, is_primary=False):
    if not value:
        return
    obj, created = AssetIdentifier.objects.get_or_create(
        asset=asset, id_type=id_type, value=value,
        defaults={"is_primary": is_primary},
    )
    if not created and is_primary and not obj.is_primary:
        obj.is_primary = True
        obj.save()


def _get_or_create_detail(asset: Asset) -> EquityDetail:
    detail, _ = EquityDetail.objects.get_or_create(asset=asset)
    return detail


class EquitySyncService:
    # --- Single Asset ---
    @staticmethod
    def sync(asset: Asset) -> bool:
        return (
            EquitySyncService.sync_profile(asset)
            and EquitySyncService.sync_quote(asset)
        )

    @staticmethod
    def sync_profile(asset: Asset) -> bool:
        if asset.asset_type != DomainType.EQUITY:
            return False

        symbol = _get_primary_ticker(asset)
        if not symbol:
            logger.warning(f"No primary ticker for {asset}")
            return False

        profile = fetch_equity_profile(symbol)
        if not profile:
            isin_id = asset.identifiers.filter(
                id_type=AssetIdentifier.IdentifierType.ISIN
            ).first()
            if isin_id:
                profile = search_by_isin(isin_id.value)

        detail, _ = EquityDetail.objects.get_or_create(asset=asset)

        if not profile:
            logger.warning(f"No profile for {symbol}")
            if not asset.is_custom:  # don't overwrite customs
                detail.listing_status = "DELISTED"
                detail.save()
            return False

        # Apply profile data
        for field, value in profile.items():
            if hasattr(detail, field):
                setattr(detail, field, value)

        # Promote from PENDING → ACTIVE
        if detail.listing_status == "PENDING":
            detail.listing_status = "ACTIVE"

        detail.save()
        return True

    @staticmethod
    def sync_quote(asset: Asset) -> bool:
        if asset.asset_type != DomainType.EQUITY:
            return False
        symbol = _get_primary_ticker(asset)
        if not symbol:
            return False
        quote = fetch_equity_quote(symbol)
        detail = _get_or_create_detail(asset)

        if not quote:
            detail.listing_status = "DELISTED"
            detail.save()
            return False

        _apply_fields(detail, quote)
        detail.listing_status = "ACTIVE"
        detail.save()
        return True

    # --- Bulk Sync ---
    @staticmethod
    def sync_profiles_bulk(assets: list[Asset]) -> dict:
        """
        Bulk sync equity profiles from FMP.
        - Updates fundamentals for all provided assets.
        - Promotes assets from PENDING → ACTIVE if hydration succeeds.
        - Skips custom assets (is_custom=True).
        """
        results = defaultdict(int)
        part = 0

        while True:
            profiles = fetch_equity_profiles_bulk(part)
            if not profiles:
                break

            with transaction.atomic():
                for record in profiles:
                    symbol = record.get("symbol")
                    if not symbol:
                        continue

                    identifier = AssetIdentifier.objects.filter(
                        id_type=AssetIdentifier.IdentifierType.TICKER,
                        value=symbol,
                    ).select_related("asset").first()

                    if not identifier:
                        continue

                    asset = identifier.asset
                    if asset.is_custom:
                        # Don't overwrite customs with bulk FMP data
                        continue

                    detail = _get_or_create_detail(asset)
                    _apply_fields(detail, record)

                    # Promote lifecycle if needed
                    if detail.listing_status == "PENDING":
                        detail.listing_status = "ACTIVE"

                    detail.save()
                    results["success"] += 1

            part += 1

        return dict(results)

    @staticmethod
    def sync_quotes_bulk(assets: list[Asset]) -> dict:
        symbols = {a: _get_primary_ticker(a)
                   for a in assets if _get_primary_ticker(a)}
        data = fetch_equity_quotes_bulk(list(symbols.values()))
        results = defaultdict(int)
        with transaction.atomic():
            for asset, symbol in symbols.items():
                detail = _get_or_create_detail(asset)
                quote = data.get(symbol)
                if not quote:
                    results["fail"] += 1
                    detail.listing_status = "DELISTED"
                    detail.save()
                    continue
                _apply_fields(detail, quote)
                detail.listing_status = "ACTIVE"
                detail.save()
                results["success"] += 1
        return dict(results)

    # --- Universe ---
    @staticmethod
    @transaction.atomic
    def sync_universe(exchange: str | None = None) -> dict:
        """
        Synchronize the equity universe with FMP.

        - Nightly (exchange=None): full reconciliation
        - Morning (exchange="NASDAQ"): exchange-specific pre-open sync

        Rules:
        - Real assets missing from feed → DELISTED
        - Custom assets preserved, but if ticker collides with new FMP ticker,
            they are flagged as COLLISION (not auto-upgraded)
        - New FMP tickers → created as PENDING, then hydrated into ACTIVE
        """
        records = fetch_equity_universe(exchange=exchange)
        seen = {r["symbol"] for r in records if r.get("symbol")}
        existing = AssetIdentifier.objects.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER
        ).select_related("asset")

        created, delisted, collisions = 0, 0, 0
        new_assets: list[Asset] = []

        # --- Delist missing ---
        for identifier in existing:
            asset = identifier.asset
            if asset.is_custom:
                continue  # customs never delisted automatically
            if identifier.value not in seen:
                detail = getattr(asset, "equity_detail", None)
                if detail and detail.listing_status != "DELISTED":
                    detail.listing_status = "DELISTED"
                    detail.save()
                    delisted += 1

        # --- Add new & handle collisions ---
        for r in records:
            symbol = r.get("symbol")
            if not symbol:
                continue

            identifier = AssetIdentifier.objects.filter(
                id_type=AssetIdentifier.IdentifierType.TICKER,
                value=symbol,
            ).select_related("asset").first()

            if identifier:
                asset = identifier.asset
                if asset.is_custom:
                    # Collision: preserve custom, flag it, and create new real asset
                    detail = _get_or_create_detail(asset)
                    detail.listing_status = "COLLISION"
                    detail.save()
                    collisions += 1

                    # Create the new FMP-backed asset separately
                    real_asset = Asset.objects.create(
                        asset_type=DomainType.EQUITY,
                        name=r.get("name") or r.get("companyName") or symbol,
                        currency=r.get("currency") or "USD",
                        is_custom=False,
                    )
                    _upsert_identifier(
                        real_asset, AssetIdentifier.IdentifierType.TICKER, symbol, True
                    )
                    EquityDetail.objects.create(
                        asset=real_asset,
                        exchange=r.get("exchangeShortName") or r.get(
                            "exchange"),
                        country=r.get("country"),
                        listing_status="PENDING",  # hydrated below
                    )
                    new_assets.append(real_asset)
                continue

            # --- Brand new IPO ---
            asset = Asset.objects.create(
                asset_type=DomainType.EQUITY,
                name=r.get("name") or r.get("companyName") or symbol,
                currency=r.get("currency"),
                is_custom=False,
            )
            _upsert_identifier(
                asset, AssetIdentifier.IdentifierType.TICKER, symbol, True
            )
            EquityDetail.objects.create(
                asset=asset,
                exchange=r.get("exchangeShortName") or r.get("exchange"),
                country=r.get("country"),
                listing_status="PENDING",  # hydrated below
            )
            created += 1
            new_assets.append(asset)

        # --- Hydrate new assets ---
        hydrated_profiles, hydrated_quotes = 0, 0
        if new_assets:
            hydrated_profiles = EquitySyncService.sync_profiles_bulk(
                new_assets).get("success", 0)
            hydrated_quotes = EquitySyncService.sync_quotes_bulk(
                new_assets).get("success", 0)

            # Mark as ACTIVE if hydration succeeded
            for asset in new_assets:
                detail = getattr(asset, "equity_detail", None)
                if detail and detail.listing_status == "PENDING":
                    if hydrated_profiles > 0 or hydrated_quotes > 0:
                        detail.listing_status = "ACTIVE"
                        detail.save()

        logger.info(
            f"Universe sync ({exchange or 'ALL'}): "
            f"+{created}, collisions={collisions}, delisted={delisted}, "
            f"hydrated profiles={hydrated_profiles}, quotes={hydrated_quotes}"
        )

        return {
            "created": created,
            "collisions": collisions,
            "delisted": delisted,
            "hydrated_profiles": hydrated_profiles,
            "hydrated_quotes": hydrated_quotes,
            "new_assets": new_assets,
        }

    # --- Create new ---

    @staticmethod
    def create_from_symbol(symbol: str) -> Asset:
        symbol = symbol.upper().strip()
        identifier = AssetIdentifier.objects.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER, value=symbol
        ).select_related("asset").first()
        if identifier:
            return identifier.asset

        profile, quote = fetch_equity_profile(
            symbol) or {}, fetch_equity_quote(symbol) or {}
        with transaction.atomic():
            if not profile and not quote:  # Custom fallback
                asset = Asset.objects.create(
                    asset_type=DomainType.EQUITY,
                    name=symbol, currency="USD", is_custom=True,
                )
                _upsert_identifier(
                    asset, AssetIdentifier.IdentifierType.TICKER, symbol, True)
                EquityDetail.objects.create(
                    asset=asset, listing_status="CUSTOM")
                return asset

            asset = Asset.objects.create(
                asset_type=DomainType.EQUITY,
                name=profile.get("companyName") or symbol,
                currency=profile.get("currency"), is_custom=False,
            )
            _upsert_identifier(
                asset, AssetIdentifier.IdentifierType.TICKER, symbol, True)
            for id_type, key in {
                AssetIdentifier.IdentifierType.ISIN: "isin",
                AssetIdentifier.IdentifierType.CUSIP: "cusip",
                AssetIdentifier.IdentifierType.CIK: "cik",
            }.items():
                _upsert_identifier(asset, id_type, profile.get(key))
            detail = EquityDetail.objects.create(
                asset=asset,
                exchange=profile.get("exchange") or profile.get(
                    "exchangeShortName"),
                country=profile.get("country"),
                listing_status="ACTIVE",
            )
            _apply_fields(detail, profile)
            _apply_fields(detail, quote)
            detail.save()
        return asset
