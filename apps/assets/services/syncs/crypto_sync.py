import logging
from collections import defaultdict
from django.db import transaction

from assets.models.assets import Asset, AssetIdentifier
from assets.models.details.crypto_detail import CryptoDetail
from assets.models.market_data_cache import MarketDataCache
from core.types import DomainType

from external_data.fmp.crypto.fetchers import (
    fetch_crypto_quote,
    fetch_crypto_quote_short,
    fetch_crypto_quotes_bulk,
    fetch_crypto_universe,
)
from external_data.fmp.crypto.utils import split_crypto_pair, clean_crypto_name

logger = logging.getLogger(__name__)


class CryptoSyncService:

    # ----------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------
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

        # Update primary PAIR symbol
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

        # Base symbol (non-primary)
        AssetIdentifier.objects.get_or_create(
            asset=asset,
            id_type=AssetIdentifier.IdentifierType.BASE_SYMBOL,
            value=base_symbol,
        )

    # ----------------------------------------------------------------------
    # Apply Data
    # ----------------------------------------------------------------------
    @staticmethod
    def _apply_profile(asset: Asset, detail: CryptoDetail, data: dict):
        for field, value in data.items():

            if field.startswith("asset__"):
                _, attr = field.split("__", 1)
                setattr(asset, attr, value)

            elif hasattr(detail, field):
                setattr(detail, field, value)

        asset.save()
        detail.save()

    @staticmethod
    def _apply_quote(asset: Asset, data: dict):
        cache, _ = MarketDataCache.objects.get_or_create(asset=asset)

        for field, value in data.items():
            if hasattr(cache, field):
                setattr(cache, field, value)

        cache.save()
        return cache

    # ----------------------------------------------------------------------
    # Single Sync
    # ----------------------------------------------------------------------
    @staticmethod
    def sync(asset: Asset) -> bool:
        return (
            CryptoSyncService.sync_profile(asset)
            and CryptoSyncService.sync_quote(asset)
        )

    @staticmethod
    def sync_profile(asset: Asset) -> bool:
        if asset.asset_type != DomainType.CRYPTO:
            return False

        pair = CryptoSyncService._get_primary_pair(asset)
        if not pair:
            return False

        # HERE: use full quote as profile+quote
        profile = fetch_crypto_quote(pair)
        if not profile:
            return False

        base, quote = split_crypto_pair(pair)
        CryptoSyncService._update_identifiers(
            asset, pair, base, quote or "USD")

        detail = CryptoSyncService._get_or_create_detail(asset)
        CryptoSyncService._apply_profile(asset, detail, profile)

        return True

    @staticmethod
    def sync_quote(asset: Asset) -> bool:
        if asset.asset_type != DomainType.CRYPTO:
            return False

        pair = CryptoSyncService._get_primary_pair(asset)
        if not pair:
            return False

        quote = fetch_crypto_quote_short(pair)
        if not quote:
            return False

        CryptoSyncService._apply_quote(asset, quote)
        return True

    # ----------------------------------------------------------------------
    # Bulk Quotes
    # ----------------------------------------------------------------------
    @staticmethod
    def sync_quotes_bulk(assets: list[Asset]) -> dict:
        results = defaultdict(int)

        pairs = {
            a: CryptoSyncService._get_primary_pair(a)
            for a in assets
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

    # ----------------------------------------------------------------------
    # Universe Sync
    # ----------------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def sync_universe(dry_run: bool = False) -> dict:
        universe = fetch_crypto_universe()

        created = 0
        updated = 0

        for rec in universe:
            pair = rec.get("symbol")
            name = rec.get("name")
            exchange = rec.get("exchange")

            if not pair:
                continue

            base, quote = split_crypto_pair(pair)
            name_clean = clean_crypto_name(name)

            # Check if asset exists
            ident = AssetIdentifier.objects.filter(
                id_type=AssetIdentifier.IdentifierType.PAIR_SYMBOL,
                value=pair
            ).select_related("asset").first()

            # -----------------------------
            # Existing → update
            # -----------------------------
            if ident:
                asset = ident.asset
                detail = CryptoSyncService._get_or_create_detail(asset)

                changed = False

                if asset.name != name_clean:
                    asset.name = name_clean
                    changed = True

                if asset.currency != quote:
                    asset.currency = quote
                    changed = True

                if detail.exchange != exchange:
                    detail.exchange = exchange
                    changed = True

                if changed and not dry_run:
                    asset.save()
                    detail.save()
                    updated += 1

                continue

            # -----------------------------
            # New → create
            # -----------------------------
            created += 1
            if dry_run:
                continue

            asset = Asset.objects.create(
                asset_type=DomainType.CRYPTO,
                name=name_clean,
                currency=quote,
                is_custom=False,
            )

            CryptoSyncService._update_identifiers(asset, pair, base, quote)

            CryptoDetail.objects.create(
                asset=asset,
                exchange=exchange,
            )

        return {
            "created": created,
            "updated": updated,
        }

    # ----------------------------------------------------------------------
    # Create From Symbol
    # ----------------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def create_from_symbol(symbol: str) -> Asset:
        """
        Create or fetch a crypto asset from either:
        - BASE symbol (e.g. BTC)
        - PAIR symbol (e.g. BTCUSD)

        Steps:
        - Normalize base → BTCUSD
        - Check existing asset
        - Fetch full quote
        - Create asset + identifiers + detail
        - Attach market data
        """
        symbol = symbol.upper().strip()

        # Normalize BTC → BTCUSD
        if len(symbol) <= 4:  # Assume base symbol (BTC, ETH, SOL, etc)
            pair_symbol = f"{symbol}USD"
        else:
            pair_symbol = symbol

        # Check existing identifier
        ident = AssetIdentifier.objects.filter(
            id_type=AssetIdentifier.IdentifierType.PAIR_SYMBOL,
            value=pair_symbol
        ).select_related("asset").first()

        if ident:
            return ident.asset

        # Fetch full quote
        profile = fetch_crypto_quote(pair_symbol)
        if not profile:
            logger.warning(
                f"No crypto data for {symbol}, creating as custom asset.")

            # Create a custom asset (user-defined token)
            asset = Asset.objects.create(
                asset_type=DomainType.CRYPTO,
                name=symbol,
                currency="USD",
                is_custom=True,
            )

            AssetIdentifier.objects.create(
                asset=asset,
                id_type=AssetIdentifier.IdentifierType.PAIR_SYMBOL,
                value=pair_symbol,
                is_primary=True,
            )
            return asset

        # Create asset
        asset = Asset.objects.create(
            asset_type=DomainType.CRYPTO,
            name=profile.get("asset__name") or symbol,
            currency=profile.get("quote_currency", "USD"),
            is_custom=False,
        )

        base, quote = split_crypto_pair(pair_symbol)

        # Identifiers
        CryptoSyncService._update_identifiers(asset, pair_symbol, base, quote)

        # Detail
        detail = CryptoDetail.objects.create(
            asset=asset,
            exchange=profile.get("exchange"),
        )
        CryptoSyncService._apply_profile(asset, detail, profile)

        # Cache market data
        CryptoSyncService._apply_quote(asset, profile)

        logger.info(f"Created new crypto asset: {asset.name} ({pair_symbol})")
        return asset
