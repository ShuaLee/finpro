import logging
from collections import defaultdict
from django.db import transaction

from apps.assets.models.asset_core.asset import Asset, AssetIdentifier, AssetType
from assets.models.details.equity_detail import EquityDetail
from assets.models.market_data_cache import MarketDataCache

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

from fx.services.utils import resolve_fx_currency, resolve_country

logger = logging.getLogger(__name__)


# ------------------------------------------------------------
# Helper: get system asset type for equities
# ------------------------------------------------------------
def get_system_asset_type() -> AssetType:
    return AssetType.objects.get(slug="equity", is_system=True)


class EquitySyncService:

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------
    @staticmethod
    def _get_primary_ticker(asset: Asset) -> str | None:
        ident = asset.identifiers.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER,
            is_primary=True,
        ).first()
        return ident.value if ident else None

    @staticmethod
    def _resolve_identifier(asset: Asset):
        """Fallback identifier search: ISIN → CUSIP → CIK"""
        for id_type in [
            AssetIdentifier.IdentifierType.ISIN,
            AssetIdentifier.IdentifierType.CUSIP,
            AssetIdentifier.IdentifierType.CIK,
        ]:
            ident = asset.identifiers.filter(id_type=id_type).first()
            if ident:
                return id_type, ident.value
        return None

    @staticmethod
    def _search_by_identifier(id_type: str, value: str):
        try:
            if id_type == AssetIdentifier.IdentifierType.ISIN:
                return fetch_equity_by_isin(value)
            if id_type == AssetIdentifier.IdentifierType.CUSIP:
                return fetch_equity_by_cusip(value)
            if id_type == AssetIdentifier.IdentifierType.CIK:
                return fetch_equity_by_cik(value)
        except Exception as e:
            logger.error(
                f"Identifier lookup failed ({id_type}={value}): {e}", exc_info=True
            )
        return None

    @staticmethod
    def _get_or_create_detail(asset: Asset) -> EquityDetail:
        return EquityDetail.objects.get_or_create(asset=asset)[0]

    @staticmethod
    def _update_ticker_identifier(asset: Asset, new_symbol: str):
        """Set ticker as primary identifier, demote old if needed."""
        new_symbol = new_symbol.upper()

        old = asset.identifiers.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER,
            is_primary=True
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

    # ------------------------------------------------------------
    # Apply Profile + Quote Fields
    # ------------------------------------------------------------
    @staticmethod
    def _apply_fields(asset: Asset, detail: EquityDetail | None, data: dict, is_quote=False):

        if not isinstance(data, dict):
            return None

        # -------------------------
        # Quote fields → MarketDataCache
        # -------------------------
        if is_quote:
            cache, _ = MarketDataCache.objects.get_or_create(asset=asset)
            for field, value in data.items():
                if hasattr(cache, field):
                    setattr(cache, field, value)
            cache.save()
            return cache

        # -------------------------
        # Profile fields → Asset + EquityDetail
        # -------------------------
        for field, value in data.items():

            # asset__prefix → asset attribute
            if field.startswith("asset__"):
                attr = field.split("__", 1)[1]

                if attr == "currency" and value:
                    try:
                        asset.currency = resolve_fx_currency(value)
                    except Exception:
                        pass
                    continue

                if hasattr(asset, attr):
                    setattr(asset, attr, value)

            # detail field
            elif detail and hasattr(detail, field):
                if field == "country":
                    detail.country = resolve_country(value)
                else:
                    setattr(detail, field, value)

        asset.save()
        if detail:
            detail.save()

        return detail

    # ------------------------------------------------------------
    # Single Asset Sync
    # ------------------------------------------------------------
    @staticmethod
    def sync(asset: Asset) -> bool:
        if asset.asset_type.slug != "equity":
            return False

        return (
            EquitySyncService.sync_profile(asset) and
            EquitySyncService.sync_quote(asset)
        )

    @staticmethod
    def sync_profile(asset: Asset) -> bool:
        if asset.asset_type.slug != "equity":
            return False

        ticker = EquitySyncService._get_primary_ticker(asset)
        profile = fetch_equity_profile(ticker) if ticker else None
        detail = EquitySyncService._get_or_create_detail(asset)

        # -------------------------
        # Case 1: Profile by ticker
        # -------------------------
        if profile:
            if "symbol" not in profile:
                logger.warning(
                    f"Profile missing 'symbol' for {ticker}: {profile}")
                return False

            if ticker and profile["symbol"].upper() != ticker.upper():
                EquitySyncService._update_ticker_identifier(
                    asset, profile["symbol"])

            EquitySyncService._apply_fields(asset, detail, profile)
            EquitySyncService.hydrate_identifiers(asset, profile)

            if detail.listing_status == "PENDING":
                detail.listing_status = "ACTIVE"
                detail.save()

            return True

        # -------------------------
        # Case 2: Fallback by ISIN/CUSIP/CIK
        # -------------------------
        resolved = EquitySyncService._resolve_identifier(asset)
        if resolved:
            id_type, value = resolved
            profile = EquitySyncService._search_by_identifier(id_type, value)

            if profile and profile.get("symbol"):
                EquitySyncService._update_ticker_identifier(
                    asset, profile["symbol"])
                EquitySyncService._apply_fields(asset, detail, profile)
                EquitySyncService.hydrate_identifiers(asset, profile)

                if detail.listing_status == "PENDING":
                    detail.listing_status = "ACTIVE"
                detail.save()
                return True

        logger.warning(f"No profile found for {asset}")
        return False

    @staticmethod
    def sync_quote(asset: Asset) -> bool:

        if asset.asset_type.slug != "equity":
            return False

        ticker = EquitySyncService._get_primary_ticker(asset)
        quote = fetch_equity_quote(ticker) if ticker else None

        # fallback: try identifiers
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
            if detail and not asset.is_custom:
                detail.listing_status = "DELISTED"
                detail.save()
            return False

        EquitySyncService._apply_fields(asset, None, quote, is_quote=True)

        detail = getattr(asset, "equity_detail", None)
        if detail and detail.listing_status in ("PENDING", "DELISTED"):
            detail.listing_status = "ACTIVE"
            detail.save()

        return True

    @staticmethod
    def sync_profile_multi(asset: Asset) -> bool:
        """
        Handles cases where FMP returns multiple profiles for a symbol.
        Syncs *all* matching profiles in the result set, not just the exact one.
        """
        if asset.asset_type.slug != "equity":
            return False

        ticker = EquitySyncService._get_primary_ticker(asset)
        if not ticker:
            return False

        from external_data.fmp.equities.fetchers import fetch_equity_profiles_multi
        profiles = fetch_equity_profiles_multi(ticker)

        if not profiles:
            logger.warning(f"No profiles returned in multi-fetch for {ticker}")
            return False

        found_any = False

        for profile in profiles:
            symbol = profile.get("symbol")
            if not symbol:
                continue

            ident = AssetIdentifier.objects.filter(
                id_type=AssetIdentifier.IdentifierType.TICKER,
                value=symbol
            ).select_related("asset").first()

            if not ident:
                continue

            matched_asset = ident.asset

            if matched_asset.asset_type.slug != "equity":
                continue

            detail = EquitySyncService._get_or_create_detail(matched_asset)

            if symbol != EquitySyncService._get_primary_ticker(matched_asset):
                EquitySyncService._update_ticker_identifier(
                    matched_asset, symbol)

            EquitySyncService._apply_fields(matched_asset, detail, profile)
            EquitySyncService.hydrate_identifiers(matched_asset, profile)

            if detail.listing_status == "PENDING":
                detail.listing_status = "ACTIVE"
                detail.save()

            found_any = True

        return found_any

    # ------------------------------------------------------------
    # Bulk Sync
    # ------------------------------------------------------------

    @staticmethod
    def sync_profiles_bulk(assets: list[Asset]) -> dict:
        results = defaultdict(int)
        part = 0
        empty = 0

        while True:
            profiles = fetch_equity_profiles_bulk(part)
            if not profiles:
                empty += 1
                if empty >= 2:
                    break
                part += 1
                continue

            with transaction.atomic():
                for rec in profiles:
                    symbol = rec.get("symbol")
                    if not symbol:
                        continue

                    ident = AssetIdentifier.objects.filter(
                        id_type=AssetIdentifier.IdentifierType.TICKER,
                        value=symbol
                    ).select_related("asset").first()

                    if not ident:
                        continue

                    asset = ident.asset

                    if asset.asset_type.slug != "equity":
                        continue

                    if asset.is_custom:
                        continue

                    detail = EquitySyncService._get_or_create_detail(asset)

                    EquitySyncService._apply_fields(asset, detail, rec)
                    EquitySyncService.hydrate_identifiers(asset, rec)

                    if detail.listing_status == "PENDING":
                        detail.listing_status = "ACTIVE"
                    detail.save()

                    results["success"] += 1

            part += 1

        return dict(results)

    @staticmethod
    def sync_quotes_bulk(assets: list[Asset]) -> dict:
        results = defaultdict(int)

        symbols = {
            a: EquitySyncService._get_primary_ticker(a)
            for a in assets if a.asset_type.slug == "equity"
        }

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

    # ------------------------------------------------------------
    # Universe Sync
    # ------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def sync_universe(exchange: str | None = None, dry_run: bool = False) -> dict:

        records = fetch_equity_universe()
        if exchange:
            records = [r for r in records if r.get(
                "exchangeShortName") == exchange]

        seen = {r["symbol"] for r in records if r.get("symbol")}

        existing = AssetIdentifier.objects.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER,
            asset__asset_type__slug="equity",
        ).select_related("asset")

        equity_type = AssetType.objects.get(slug="equity", is_system=True)

        created = delisted = collisions = renamed = refreshed = 0
        new_assets: list[Asset] = []

        # ---------------------------
        # EXISTING EQUITIES
        # ---------------------------
        for identifier in existing:

            asset = identifier.asset
            ticker = identifier.value
            detail = getattr(asset, "equity_detail", None)

            # custom assets → leave alone
            if asset.is_custom:
                continue

            # --- case: still exists in universe (normal refresh)
            if ticker in seen:

                profile = fetch_equity_profile(ticker)
                if not profile:
                    continue

                updated = False

                new_name = profile.get("companyName") or profile.get("name")
                if new_name and asset.name != new_name:
                    asset.name = new_name
                    updated = True

                # currency
                if profile.get("currency"):
                    cur = resolve_fx_currency(profile["currency"])
                    if cur and asset.currency != cur:
                        asset.currency = cur
                        updated = True

                # detail fields
                if detail:
                    for field in ["sector", "industry", "exchangeShortName", "country"]:
                        new_val = profile.get(field)
                        if not new_val:
                            continue

                        if field == "country":
                            resolved = resolve_country(new_val)
                            if resolved and detail.country != resolved:
                                detail.country = resolved
                                updated = True
                            continue

                        if getattr(detail, field, None) != new_val:
                            setattr(detail, field, new_val)
                            updated = True

                if updated and not dry_run:
                    asset.save()
                    detail and detail.save()
                    refreshed += 1

                continue

            # -------------------------
            # missing → check rename or delist
            # -------------------------
            resolved_id = EquitySyncService._resolve_identifier(asset)
            if not resolved_id:
                delisted += 1
                if not dry_run and detail:
                    detail.listing_status = "DELISTED"
                    detail.save()
                continue

            id_type, id_val = resolved_id
            alt_profile = EquitySyncService._search_by_identifier(
                id_type, id_val)

            if not alt_profile:
                delisted += 1
                if not dry_run and detail:
                    detail.listing_status = "DELISTED"
                    detail.save()
                continue

            new_symbol = alt_profile.get("symbol")

            if not new_symbol or new_symbol == ticker:
                delisted += 1
                continue

            # rename
            renamed += 1
            if not dry_run:
                EquitySyncService._update_ticker_identifier(asset, new_symbol)
                EquitySyncService._apply_fields(asset, detail, alt_profile)

                cur = alt_profile.get("currency")
                if cur:
                    asset.currency = resolve_fx_currency(cur)

                asset.save()

                if detail and detail.listing_status == "DELISTED":
                    detail.listing_status = "ACTIVE"
                    detail.save()

        # ---------------------------
        # NEW IPOs
        # ---------------------------
        for r in records:
            symbol = r.get("symbol")
            if not symbol:
                continue

            exists = AssetIdentifier.objects.filter(
                id_type=AssetIdentifier.IdentifierType.TICKER,
                value=symbol
            ).exists()

            if exists:
                continue

            created += 1
            if dry_run:
                continue

            asset = Asset.objects.create(
                asset_type=equity_type,
                name=r.get("name") or r.get("companyName") or symbol,
                currency=resolve_fx_currency(r.get("currency")),
                is_custom=False,
            )

            EquitySyncService._update_ticker_identifier(asset, symbol)

            detail = EquityDetail.objects.create(
                asset=asset,
                exchange=r.get("exchangeShortName") or r.get("exchange"),
                country=resolve_country(r.get("country")),
                listing_status="PENDING",
            )

            EquitySyncService._apply_fields(asset, detail, r)
            new_assets.append(asset)

        # ---------------------------
        # Hydrate profile for new assets
        # ---------------------------
        hydrated = 0
        if new_assets and not dry_run:
            try:
                hydrated = EquitySyncService.sync_profiles_bulk(
                    new_assets).get("success", 0)

                for asset in new_assets:
                    detail = getattr(asset, "equity_detail", None)
                    if detail and detail.listing_status == "PENDING" and hydrated > 0:
                        detail.listing_status = "ACTIVE"
                        detail.save()

            except Exception:
                pass

        return {
            "created": created,
            "renamed": renamed,
            "refreshed": refreshed,
            "collisions": collisions,
            "delisted": delisted,
            "hydrated_profiles": hydrated,
            "hydrated_quotes": 0,
            "new_assets": new_assets if not dry_run else [],
        }

    # ------------------------------------------------------------
    # Seed Universe
    # ------------------------------------------------------------
    @staticmethod
    def seed_universe() -> dict:
        return EquitySyncService.sync_universe(exchange=None, dry_run=False)

    # ------------------------------------------------------------
    # Create From Symbol
    # ------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def create_from_symbol(symbol: str) -> Asset:

        symbol = symbol.upper().strip()

        # already exists
        ident = AssetIdentifier.objects.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER,
            value=symbol
        ).select_related("asset").first()

        if ident:
            return ident.asset

        profile = fetch_equity_profile(symbol) or {}
        quote = fetch_equity_quote(symbol)

        equity_type = AssetType.objects.get(slug="equity", is_system=True)

        # -----------------------------
        # no provider → create custom asset
        # -----------------------------
        if not profile:

            asset = Asset.objects.create(
                asset_type=equity_type,
                name=symbol,
                currency=resolve_fx_currency("USD"),
                is_custom=True,
            )

            EquitySyncService._update_ticker_identifier(asset, symbol)

            EquityDetail.objects.create(
                asset=asset,
                listing_status="CUSTOM",
            )

            return asset

        # -----------------------------
        # provider profile → create real asset
        # -----------------------------
        asset = Asset.objects.create(
            asset_type=equity_type,
            name=profile.get("companyName") or profile.get("name") or symbol,
            currency=resolve_fx_currency(profile.get("currency")),
            is_custom=False,
        )

        EquitySyncService._update_ticker_identifier(asset, symbol)

        # identifiers
        for id_type, key in {
            AssetIdentifier.IdentifierType.ISIN: "isin",
            AssetIdentifier.IdentifierType.CUSIP: "cusip",
            AssetIdentifier.IdentifierType.CIK: "cik",
        }.items():
            value = profile.get(key)
            if value:
                AssetIdentifier.objects.get_or_create(
                    asset=asset, id_type=id_type, value=value
                )

        # detail
        detail = EquityDetail.objects.create(
            asset=asset,
            exchange=profile.get("exchange") or profile.get(
                "exchangeShortName"),
            country=resolve_country(profile.get("country")),
            listing_status="ACTIVE",
        )

        EquitySyncService._apply_fields(asset, detail, profile)

        # quote
        if quote:
            EquitySyncService._apply_fields(asset, None, quote, is_quote=True)

        return asset

    # ------------------------------------------------------------
    # Identifier hydration
    # ------------------------------------------------------------
    @staticmethod
    def hydrate_identifiers(asset: Asset, data: dict):
        id_map = {
            "isin": AssetIdentifier.IdentifierType.ISIN,
            "cusip": AssetIdentifier.IdentifierType.CUSIP,
            "cik": AssetIdentifier.IdentifierType.CIK,
        }
        for key, id_type in id_map.items():
            if key in data and data[key]:
                AssetIdentifier.objects.get_or_create(
                    asset=asset, id_type=id_type, value=data[key]
                )
