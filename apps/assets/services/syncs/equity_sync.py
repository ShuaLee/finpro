import logging
from collections import defaultdict
from django.db import transaction

from assets.models.assets import Asset, AssetIdentifier
from assets.models.details.equity_detail import EquityDetail
from assets.models.market_data_cache import MarketDataCache
from core.types import DomainType

from external_data.fmp.equities.fetchers import (
    fetch_equity_profile,
    fetch_equity_by_isin,
    fetch_equity_by_cusip,
    fetch_equity_by_cik,
    fetch_equity_quote,
    fetch_equity_profiles_bulk,
    fetch_equity_quotes_bulk,
    fetch_equity_universe,
)
from external_data.fmp.equities.mappings import EQUITY_PROFILE_MAP, EQUITY_QUOTE_MAP

logger = logging.getLogger(__name__)


class EquitySyncService:
    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    @staticmethod
    def _get_primary_ticker(asset: Asset) -> str | None:
        primary = asset.identifiers.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER,
            is_primary=True,
        ).first()
        return primary.value if primary else None

    @staticmethod
    def _resolve_identifier(asset: Asset) -> tuple[str, str] | None:
        """Priority fallback order: ISIN → CUSIP → CIK"""
        for id_type in [
            AssetIdentifier.IdentifierType.ISIN,
            AssetIdentifier.IdentifierType.CUSIP,
            AssetIdentifier.IdentifierType.CIK,
        ]:
            identifier = asset.identifiers.filter(id_type=id_type).first()
            if identifier:
                return id_type, identifier.value
        return None

    @staticmethod
    def _search_by_identifier(id_type: str, value: str) -> dict | None:
        try:
            if id_type == AssetIdentifier.IdentifierType.ISIN:
                return fetch_equity_by_isin(value)
            elif id_type == AssetIdentifier.IdentifierType.CUSIP:
                return fetch_equity_by_cusip(value)
            elif id_type == AssetIdentifier.IdentifierType.CIK:
                return fetch_equity_by_cik(value)
            else:
                logger.warning(f"Unsupported identifier type: {id_type}")
        except Exception as e:
            logger.error(
                f"Identifier lookup failed ({id_type}: {value}): {e}", exc_info=True
            )
        return None

    @staticmethod
    def _get_or_create_detail(asset: Asset) -> EquityDetail:
        return EquityDetail.objects.get_or_create(asset=asset)[0]

    @staticmethod
    def _update_ticker_identifier(asset: Asset, new_symbol: str) -> None:
        """Promote new_symbol as the primary ticker, demote old one if needed."""
        new_symbol = new_symbol.upper().strip()
        old = asset.identifiers.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER, is_primary=True
        ).first()
        if old and old.value != new_symbol:
            old.is_primary = False
            old.save()

        ident, _ = AssetIdentifier.objects.get_or_create(
            asset=asset,
            id_type=AssetIdentifier.IdentifierType.TICKER,
            value=new_symbol,
        )
        if not ident.is_primary:
            ident.is_primary = True
            ident.save()

    # -------------------------------------------------------------------------
    # Core Field Application Logic
    # -------------------------------------------------------------------------
    @staticmethod
    def _apply_fields(asset: Asset, detail: EquityDetail | None, data: dict, is_quote: bool = False):
        """
        Apply normalized fields from provider → Asset + EquityDetail + MarketDataCache.
        """
        mapping = EQUITY_QUOTE_MAP if is_quote else EQUITY_PROFILE_MAP

        # Quote data → MarketDataCache
        if is_quote:
            cache, _ = MarketDataCache.objects.get_or_create(asset=asset)
            for src_key, dest_field in mapping.items():
                if src_key not in data:
                    continue
                value = data[src_key]
                if hasattr(cache, dest_field):
                    setattr(cache, dest_field, value)
            cache.save()
            return cache

        # Profile data → Asset + EquityDetail
        for src_key, dest_field in mapping.items():
            if src_key not in data:
                continue
            value = data[src_key]

            if dest_field.startswith("asset__"):
                field = dest_field.split("__", 1)[1]
                if hasattr(asset, field):
                    setattr(asset, field, value)
            elif detail and hasattr(detail, dest_field):
                setattr(detail, dest_field, value)

        asset.save()
        if detail:
            detail.save()
        return detail

    # -------------------------------------------------------------------------
    # Single Asset Sync
    # -------------------------------------------------------------------------
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

        ticker = EquitySyncService._get_primary_ticker(asset)
        profile = fetch_equity_profile(ticker) if ticker else None
        detail = EquitySyncService._get_or_create_detail(asset)

        if profile:
            if ticker and profile.get("symbol") and profile["symbol"] != ticker:
                EquitySyncService._update_ticker_identifier(
                    asset, profile["symbol"])

            EquitySyncService._apply_fields(
                asset, detail, profile, is_quote=False)
            if detail.listing_status == "PENDING":
                detail.listing_status = "ACTIVE"
            detail.save()
            return True

        resolved = EquitySyncService._resolve_identifier(asset)
        if resolved:
            id_type, value = resolved
            profile = EquitySyncService._search_by_identifier(id_type, value)

            if profile and profile.get("symbol"):
                EquitySyncService._update_ticker_identifier(
                    asset, profile["symbol"])
                EquitySyncService._apply_fields(
                    asset, detail, profile, is_quote=False)
                if detail.listing_status == "PENDING":
                    detail.listing_status = "ACTIVE"
                detail.save()
                return True

        if not asset.is_custom:
            detail.listing_status = "DELISTED"
            detail.save()
        logger.warning(f"No profile found for {asset}")
        return False

    @staticmethod
    def sync_quote(asset: Asset) -> bool:
        if asset.asset_type != DomainType.EQUITY:
            return False

        ticker = EquitySyncService._get_primary_ticker(asset)
        quote = fetch_equity_quote(ticker) if ticker else None

        if not quote:
            resolved = EquitySyncService._resolve_identifier(asset)
            if resolved:
                id_type, value = resolved
                profile = EquitySyncService._search_by_identifier(
                    id_type, value)
                if profile and profile.get("symbol"):
                    new_symbol = profile["symbol"]
                    EquitySyncService._update_ticker_identifier(
                        asset, new_symbol)
                    quote = fetch_equity_quote(new_symbol)

        if not quote:
            detail = getattr(asset, "equity_detail", None)
            if detail:
                detail.listing_status = "DELISTED"
                detail.save()
            return False

        EquitySyncService._apply_fields(asset, None, quote, is_quote=True)

        detail = getattr(asset, "equity_detail", None)
        if detail and detail.listing_status in ("PENDING", "DELISTED"):
            detail.listing_status = "ACTIVE"
            detail.save()
        return True

    # -------------------------------------------------------------------------
    # Bulk Sync
    # -------------------------------------------------------------------------
    @staticmethod
    def sync_profiles_bulk(assets: list[Asset]) -> dict:
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
                        continue

                    detail = EquitySyncService._get_or_create_detail(asset)

                    if record["symbol"] != symbol:
                        EquitySyncService._update_ticker_identifier(
                            asset, record["symbol"])

                    EquitySyncService._apply_fields(
                        asset, detail, record, is_quote=False)
                    if detail.listing_status == "PENDING":
                        detail.listing_status = "ACTIVE"
                        detail.save()
                    results["success"] += 1

            part += 1

        return dict(results)

    @staticmethod
    def sync_quotes_bulk(assets: list[Asset]) -> dict:
        results = defaultdict(int)
        symbols = {a: EquitySyncService._get_primary_ticker(a) for a in assets}
        symbols = {a: s for a, s in symbols.items() if s}

        data = fetch_equity_quotes_bulk(list(symbols.values()))
        data_map = {d["symbol"]: d for d in data if d.get("symbol")}

        with transaction.atomic():
            for asset, symbol in symbols.items():
                quote = data_map.get(symbol)

                if not quote:
                    resolved = EquitySyncService._resolve_identifier(asset)
                    if resolved:
                        id_type, value = resolved
                        profile = EquitySyncService._search_by_identifier(
                            id_type, value)
                        if profile and profile.get("symbol"):
                            new_symbol = profile["symbol"]
                            EquitySyncService._update_ticker_identifier(
                                asset, new_symbol)
                            quote = data_map.get(new_symbol)

                if not quote:
                    detail = getattr(asset, "equity_detail", None)
                    if detail:
                        detail.listing_status = "DELISTED"
                        detail.save()
                    results["fail"] += 1
                    continue

                EquitySyncService._apply_fields(
                    asset, None, quote, is_quote=True)
                detail = getattr(asset, "equity_detail", None)
                if detail and detail.listing_status in ("PENDING", "DELISTED"):
                    detail.listing_status = "ACTIVE"
                    detail.save()
                results["success"] += 1

        return dict(results)

    # -------------------------------------------------------------------------
    # Universe Sync + Seed
    # -------------------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def sync_universe(exchange: str | None = None, dry_run: bool = False) -> dict:
        """
        Synchronize the local DB equity universe with FMP:
        - Adds new symbols (IPOs)
        - Marks missing ones as delisted
        - Handles ticker renames & custom collisions
        - Hydrates profiles for new assets (no quotes)
        """
        records = fetch_equity_universe()
        if exchange:
            records = [r for r in records if r.get(
                "exchangeShortName") == exchange]
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
                continue
            if identifier.value not in seen:
                delisted += 1
                logger.warning(
                    f"Delisting {asset} (ticker={identifier.value})")
                if not dry_run:
                    detail = getattr(asset, "equity_detail", None)
                    if detail and detail.listing_status != "DELISTED":
                        detail.listing_status = "DELISTED"
                        detail.save()

        # --- Add new + handle collisions ---
        for r in records:
            symbol = r.get("symbol")
            if not symbol:
                continue

            identifier = AssetIdentifier.objects.filter(
                id_type=AssetIdentifier.IdentifierType.TICKER,
                value=symbol,
            ).select_related("asset").first()

            if identifier:  # already exists
                asset = identifier.asset
                if asset.is_custom:
                    collisions += 1
                    logger.info(f"Collision: custom {asset} vs {symbol}")

                    if not dry_run:
                        detail = EquitySyncService._get_or_create_detail(asset)
                        detail.listing_status = "COLLISION"
                        detail.save()

                        real_asset = Asset.objects.create(
                            asset_type=DomainType.EQUITY,
                            name=r.get("name") or r.get(
                                "companyName") or symbol,
                            currency=r.get("currency") or "USD",
                            is_custom=False,
                        )
                        EquitySyncService._update_ticker_identifier(
                            real_asset, symbol)
                        real_detail = EquityDetail.objects.create(
                            asset=real_asset,
                            exchange=r.get("exchangeShortName") or r.get(
                                "exchange"),
                            country=r.get("country"),
                            listing_status="PENDING",
                        )
                        EquitySyncService._apply_fields(
                            real_asset, real_detail, r, is_quote=False)
                        new_assets.append(real_asset)
                continue

            # New IPO
            created += 1
            logger.info(f"New IPO detected: {symbol}")
            if not dry_run:
                asset = Asset.objects.create(
                    asset_type=DomainType.EQUITY,
                    name=r.get("name") or r.get("companyName") or symbol,
                    currency=r.get("currency") or "USD",
                    is_custom=False,
                )
                EquitySyncService._update_ticker_identifier(asset, symbol)
                detail = EquityDetail.objects.create(
                    asset=asset,
                    exchange=r.get("exchangeShortName") or r.get("exchange"),
                    country=r.get("country"),
                    listing_status="PENDING",
                )
                EquitySyncService._apply_fields(
                    asset, detail, r, is_quote=False)
                new_assets.append(asset)

        # --- Hydrate profiles for new assets (NO QUOTES) ---
        hydrated_profiles = 0
        if new_assets and not dry_run:
            try:
                hydrated_profiles = EquitySyncService.sync_profiles_bulk(
                    new_assets).get("success", 0)
                for asset in new_assets:
                    detail = getattr(asset, "equity_detail", None)
                    if detail and detail.listing_status == "PENDING" and hydrated_profiles > 0:
                        detail.listing_status = "ACTIVE"
                        detail.save()
            except Exception as e:
                logger.error(
                    f"Bulk profile hydration failed: {e}", exc_info=True)

        # --- Logging Summary ---
        logger.info(
            f"Universe sync ({exchange or 'ALL'}){' [dry run]' if dry_run else ''}: "
            f"+{created}, collisions={collisions}, delisted={delisted}, "
            f"hydrated profiles={hydrated_profiles}"
        )

        return {
            "created": created,
            "collisions": collisions,
            "delisted": delisted,
            "hydrated_profiles": hydrated_profiles,
            "hydrated_quotes": 0,  # Explicitly no quote hydration here
            "new_assets": new_assets if not dry_run else [],
        }

    @staticmethod
    def seed_universe() -> dict:
        """
        Initial seeding of the entire equity universe into the DB.
        Fetches and stores profile data (no quote data).
        Equivalent to a full nightly universe sync with dry_run=False.
        """
        logger.info(
            "Starting initial equity universe seed (profiles only, no quotes)")

        results = EquitySyncService.sync_universe(exchange=None, dry_run=False)

        # Sanity log
        logger.info(
            f"Seed completed: +{results['created']} new, "
            f"collisions={results['collisions']}, delisted={results['delisted']}, "
            f"hydrated profiles={results['hydrated_profiles']}, "
            f"(no quotes fetched)"
        )

        return results

    # -------------------------------------------------------------------------
    # Create from Symbol
    # -------------------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def create_from_symbol(symbol: str) -> Asset:
        """
        Create or fetch an equity asset by ticker.
        - If exists → return it.
        - Else fetch profile (and optionally quote) from FMP.
        - If no data → create as custom.
        - Else → create real asset + identifiers + hydrate detail.
        """
        symbol = symbol.upper().strip()

        # --- Already exists ---
        identifier = AssetIdentifier.objects.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER,
            value=symbol,
        ).select_related("asset").first()
        if identifier:
            return identifier.asset

        # --- Fetch from provider ---
        profile = fetch_equity_profile(symbol) or {}
        quote = fetch_equity_quote(symbol) or None  # Optional, may skip

        # --- Handle missing profile (custom asset) ---
        if not profile:
            logger.warning(
                f"No profile found for {symbol}, creating as custom asset.")
            asset = Asset.objects.create(
                asset_type=DomainType.EQUITY,
                name=symbol,
                currency="USD",
                is_custom=True,
            )
            EquitySyncService._update_ticker_identifier(asset, symbol)
            EquityDetail.objects.create(asset=asset, listing_status="CUSTOM")
            return asset

        # --- Create the real asset ---
        asset = Asset.objects.create(
            asset_type=DomainType.EQUITY,
            name=profile.get("companyName") or profile.get("name") or symbol,
            currency=profile.get("currency") or "USD",
            is_custom=False,
        )
        EquitySyncService._update_ticker_identifier(asset, symbol)

        # --- Secondary Identifiers ---
        for id_type, key in {
            AssetIdentifier.IdentifierType.ISIN: "isin",
            AssetIdentifier.IdentifierType.CUSIP: "cusip",
            AssetIdentifier.IdentifierType.CIK: "cik",
        }.items():
            value = profile.get(key)
            if value:
                AssetIdentifier.objects.get_or_create(
                    asset=asset,
                    id_type=id_type,
                    value=value,
                )

        # --- Detail (profile enrichment) ---
        detail = EquityDetail.objects.create(
            asset=asset,
            exchange=profile.get("exchange") or profile.get(
                "exchangeShortName"),
            country=profile.get("country"),
            listing_status="ACTIVE",
        )
        EquitySyncService._apply_fields(asset, detail, profile, is_quote=False)
        detail.save()

        # --- MarketDataCache (optional quote) ---
        if quote:
            cache = EquitySyncService._apply_fields(
                asset, None, quote, is_quote=True)
            logger.info(f"Cached quote for {symbol}: {cache.last_price}")

        logger.info(f"Created new equity asset {symbol} ({asset.name})")
        return asset
