import logging
from collections import defaultdict
from django.db import transaction

from apps.assets.models.asset_core.asset import Asset, AssetIdentifier, AssetType
from assets.models.details.crypto_detail import CryptoDetail
from assets.models.market_data_cache import MarketDataCache

from external_data.fmp.crypto.fetchers import (
    fetch_crypto_quote,
    fetch_crypto_quote_short,
    fetch_crypto_quotes_bulk,
    fetch_crypto_universe,
)
from external_data.fmp.crypto.utils import split_crypto_pair, clean_crypto_name

from fx.services.utils import resolve_fx_currency

logger = logging.getLogger(__name__)


class CryptoSyncService:

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------
    @staticmethod
    def _get_primary_pair(asset: Asset) -> str | None:
        ident = asset.identifiers.filter(
            id_type=AssetIdentifier.IdentifierType.PAIR_SYMBOL,
            is_primary=True
        ).first()
        return ident.value if ident else None

    @staticmethod
    def _get_or_create_detail(asset: Asset) -> CryptoDetail:
        return CryptoDetail.objects.get_or_create(asset=asset)[0]

    @staticmethod
    def _update_identifiers(asset: Asset, pair_symbol: str, base_symbol: str, quote: str):

        pair_symbol = pair_symbol.upper()
        base_symbol = base_symbol.upper()

        # --- Ensure only one primary PAIR identifier ---
        existing_primary = asset.identifiers.filter(
            id_type=AssetIdentifier.IdentifierType.PAIR_SYMBOL,
            is_primary=True
        ).first()

        if existing_primary and existing_primary.value != pair_symbol:
            existing_primary.is_primary = False
            existing_primary.save()

        pair_ident, _ = AssetIdentifier.objects.get_or_create(
            asset=asset,
            id_type=AssetIdentifier.IdentifierType.PAIR_SYMBOL,
            value=pair_symbol,
        )

        if not pair_ident.is_primary:
            pair_ident.is_primary = True
            pair_ident.save()

        # --- Base symbol (non-primary) ---
        AssetIdentifier.objects.get_or_create(
            asset=asset,
            id_type=AssetIdentifier.IdentifierType.BASE_SYMBOL,
            value=base_symbol,
        )

    # ---------------------------------------------------------
    # Apply Data
    # ---------------------------------------------------------
    @staticmethod
    def _apply_profile(asset: Asset, detail: CryptoDetail, data: dict):

        asset_dirty = False
        detail_dirty = False

        # Fields allowed to update on CryptoDetail
        FMP_DETAIL_FIELDS = {"exchange"}

        for field, value in data.items():

            # ----------------------
            # Asset fields: "asset__name", "asset__currency" etc.
            # ----------------------
            if field.startswith("asset__"):
                _, attr = field.split("__", 1)

                if attr == "asset_type":
                    continue  # Never override asset type

                if attr == "currency" and value:
                    try:
                        asset.currency = resolve_fx_currency(value)
                        asset_dirty = True
                    except Exception as e:
                        logger.warning(f"FX resolve failed for {value}: {e}")
                    continue

                if hasattr(asset, attr):
                    setattr(asset, attr, value)
                    asset_dirty = True
                continue

            # ----------------------
            # CryptoDetail fields
            # ----------------------
            if field in FMP_DETAIL_FIELDS:
                setattr(detail, field, value)
                detail_dirty = True

        if asset_dirty:
            asset.save()

        if detail_dirty:
            detail.save()

    @staticmethod
    def _apply_quote(asset: Asset, data: dict):
        cache, _ = MarketDataCache.objects.get_or_create(asset=asset)

        dirty = False
        for field, value in data.items():
            if hasattr(cache, field):
                try:
                    if getattr(cache, field) != value:
                        setattr(cache, field, value)
                        dirty = True
                except Exception as e:
                    logger.warning(
                        f"Skipping quote field {field} for {asset}: {e}"
                    )

        if dirty:
            cache.save()

        return cache

    # ---------------------------------------------------------
    # Single-Asset Sync
    # ---------------------------------------------------------
    @staticmethod
    def sync(asset: Asset) -> bool:
        return (
            CryptoSyncService.sync_profile(asset)
            and CryptoSyncService.sync_quote(asset)
        )

    @staticmethod
    def sync_profile(asset: Asset) -> bool:

        if asset.asset_type.slug != "crypto":
            return False

        pair = CryptoSyncService._get_primary_pair(asset)
        if not pair:
            return False

        profile = fetch_crypto_quote(pair)
        if not profile:
            return False

        base, quote = split_crypto_pair(pair)

        CryptoSyncService._update_identifiers(asset, pair, base, quote)

        # Update currency field
        if quote:
            try:
                fx = resolve_fx_currency(quote)
                if asset.currency != fx:
                    asset.currency = fx
                    asset.save()
            except Exception:
                pass

        detail = CryptoSyncService._get_or_create_detail(asset)
        CryptoSyncService._apply_profile(asset, detail, profile)

        return True

    @staticmethod
    def sync_quote(asset: Asset) -> bool:

        if asset.asset_type.slug != "crypto":
            return False

        pair = CryptoSyncService._get_primary_pair(asset)
        if not pair:
            return False

        quote = fetch_crypto_quote_short(pair)
        if not quote:
            return False

        CryptoSyncService._apply_quote(asset, quote)
        return True

    # ---------------------------------------------------------
    # Bulk Quotes (FMP supports this)
    # ---------------------------------------------------------
    @staticmethod
    def sync_quotes_bulk(assets: list[Asset]) -> dict:
        results = defaultdict(int)

        pairs = {
            asset: CryptoSyncService._get_primary_pair(asset)
            for asset in assets
            if asset.asset_type.slug == "crypto"
        }
        pairs = {a: p for a, p in pairs.items() if p}

        data = fetch_crypto_quotes_bulk()

        with transaction.atomic():
            for asset, pair in pairs.items():
                quote = data.get(pair)
                if not quote:
                    results["fail"] += 1
                    continue

                CryptoSyncService._apply_quote(asset, quote)
                results["success"] += 1

        return dict(results)

    # ---------------------------------------------------------
    # Universe Sync (mass creation/update)
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def sync_universe(dry_run: bool = False) -> dict:

        universe = fetch_crypto_universe()
        created = 0
        updated = 0

        crypto_type = AssetType.objects.get(slug="crypto", is_system=True)

        for rec in universe:

            pair = rec.get("symbol")
            name = rec.get("name")
            exchange = rec.get("exchange")

            if not pair:
                continue

            base, quote = split_crypto_pair(pair)
            name_clean = clean_crypto_name(name)

            # Find existing
            ident = AssetIdentifier.objects.filter(
                id_type=AssetIdentifier.IdentifierType.PAIR_SYMBOL,
                value=pair
            ).select_related("asset").first()

            # ------------------
            # EXISTING ASSET
            # ------------------
            if ident:
                asset = ident.asset

                if asset.asset_type.slug != "crypto":
                    logger.warning(
                        f"Identifier {pair} attaches to non-crypto asset {asset}"
                    )
                    continue

                detail = CryptoSyncService._get_or_create_detail(asset)
                changed = False

                if asset.name != name_clean:
                    asset.name = name_clean
                    changed = True

                if quote:
                    fx = resolve_fx_currency(quote)
                    if asset.currency != fx:
                        asset.currency = fx
                        changed = True

                if detail.exchange != exchange:
                    detail.exchange = exchange
                    changed = True

                if changed and not dry_run:
                    asset.save()
                    detail.save()
                    updated += 1

                continue

            # ------------------
            # NEW ASSET
            # ------------------
            created += 1
            if dry_run:
                continue

            asset = Asset.objects.create(
                asset_type=crypto_type,
                name=name_clean,
                currency=resolve_fx_currency(quote),
                is_custom=False,
            )

            CryptoSyncService._update_identifiers(asset, pair, base, quote)

            CryptoDetail.objects.create(
                asset=asset,
                exchange=exchange,
            )

        return {"created": created, "updated": updated}

    # ---------------------------------------------------------
    # Create From Symbol
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def create_from_symbol(symbol: str) -> Asset:

        symbol = symbol.upper().strip()

        pair_symbol = (
            f"{symbol}USD"
            if len(symbol) <= 4 else symbol
        )

        crypto_type = AssetType.objects.get(slug="crypto", is_system=True)

        ident = AssetIdentifier.objects.filter(
            id_type=AssetIdentifier.IdentifierType.PAIR_SYMBOL,
            value=pair_symbol
        ).select_related("asset").first()

        if ident and ident.asset.asset_type.slug == "crypto":
            return ident.asset

        profile = fetch_crypto_quote(pair_symbol)

        # ----------------------
        # No provider data
        # ----------------------
        if not profile:
            asset = Asset.objects.create(
                asset_type=crypto_type,
                name=symbol,
                currency=resolve_fx_currency("USD"),
                is_custom=True,
            )

            AssetIdentifier.objects.create(
                asset=asset,
                id_type=AssetIdentifier.IdentifierType.PAIR_SYMBOL,
                value=pair_symbol,
                is_primary=True,
            )
            return asset

        # ----------------------
        # Valid provider data
        # ----------------------
        base, quote = split_crypto_pair(pair_symbol)

        asset = Asset.objects.create(
            asset_type=crypto_type,
            name=profile.get("name") or symbol,
            currency=resolve_fx_currency(quote),
            is_custom=False,
        )

        CryptoSyncService._update_identifiers(asset, pair_symbol, base, quote)

        detail = CryptoDetail.objects.create(
            asset=asset,
            exchange=profile.get("exchange"),
        )

        CryptoSyncService._apply_profile(asset, detail, profile)
        CryptoSyncService._apply_quote(asset, profile)

        logger.info(f"Created new crypto asset: {asset.name} ({pair_symbol})")

        return asset
