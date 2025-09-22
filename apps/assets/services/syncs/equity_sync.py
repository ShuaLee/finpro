import logging
from collections import defaultdict
from django.db import transaction

from assets.models.assets import Asset, AssetIdentifier
from assets.models.details.equity_detail import EquityDetail
from core.types import DomainType

from external_data.fmp.equities.fetchers import (
    fetch_equity_profile,
    fetch_equity_quote,
    fetch_equity_profiles_bulk,
    fetch_equity_quotes_bulk,
    fetch_equity_universe,
)
from external_data.fmp.shared.isin import search_by_isin

logger = logging.getLogger(__name__)


def _get_primary_ticker(asset: Asset) -> str | None:
    primary_id = asset.identifiers.filter(
        id_type=AssetIdentifier.IdentifierType.TICKER,
        is_primary=True,
    ).first()
    return primary_id.value if primary_id else None


class EquitySyncService:
    # --- Single Asset Sync ---
    @staticmethod
    def sync(asset: Asset) -> bool:
        return EquitySyncService.sync_profile(asset) and EquitySyncService.sync_quote(asset)

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
            detail.listing_status = "DELISTED"
            detail.save()
            return False

        for field, value in profile.items():
            if hasattr(detail, field):
                setattr(detail, field, value)

        detail.is_custom = False
        detail.listing_status = "ACTIVE"
        detail.save()
        return True

    @staticmethod
    def sync_quote(asset: Asset) -> bool:
        if asset.asset_type != DomainType.EQUITY:
            return False

        symbol = _get_primary_ticker(asset)
        if not symbol:
            logger.warning(f"No primary ticker for {asset}")
            return False

        quote = fetch_equity_quote(symbol)
        detail, _ = EquityDetail.objects.get_or_create(asset=asset)

        if not quote:
            logger.warning(f"No quote for {symbol}")
            detail.listing_status = "DELISTED"
            detail.save()
            return False

        for field, value in quote.items():
            if hasattr(detail, field):
                setattr(detail, field, value)

        detail.listing_status = "ACTIVE"
        detail.save()
        return True

    # --- Bulk Sync ---
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

                    try:
                        identifier = AssetIdentifier.objects.get(
                            id_type=AssetIdentifier.IdentifierType.TICKER,
                            value=symbol,
                        )
                        asset = identifier.asset
                    except AssetIdentifier.DoesNotExist:
                        continue

                    detail, _ = EquityDetail.objects.get_or_create(asset=asset)
                    for field, value in record.items():
                        if hasattr(detail, field):
                            setattr(detail, field, value)
                    detail.is_custom = False
                    detail.save()
                    results["success"] += 1

            part += 1

        return dict(results)

    @staticmethod
    def sync_quotes_bulk(assets: list[Asset]) -> dict:
        symbols, asset_map = [], {}
        for asset in assets:
            symbol = _get_primary_ticker(asset)
            if symbol:
                symbols.append(symbol)
                asset_map[symbol] = asset

        data = fetch_equity_quotes_bulk(symbols)
        results = defaultdict(int)

        with transaction.atomic():
            for symbol, asset in asset_map.items():
                detail, _ = EquityDetail.objects.get_or_create(asset=asset)
                quote = data.get(symbol)
                if not quote:
                    results["fail"] += 1
                    detail.listing_status = "DELISTED"
                    detail.save()
                    continue

                for field, value in quote.items():
                    if hasattr(detail, field):
                        setattr(detail, field, value)

                detail.listing_status = "ACTIVE"
                detail.save()
                results["success"] += 1

        return dict(results)

    # --- Universe Management ---
    @staticmethod
    @transaction.atomic
    def seed_universe() -> int:
        """
        Initial bulk load of all equities from FMP.
        Returns count of created assets.
        """
        records = fetch_equity_universe()
        created_count = 0

        for record in records:
            symbol = record.get("symbol")
            name = record.get("name")
            exchange = record.get("exchangeShortName")

            if not symbol:
                continue

            # Skip if ticker already exists
            if AssetIdentifier.objects.filter(
                id_type=AssetIdentifier.IdentifierType.TICKER,
                value=symbol,
            ).exists():
                continue

            asset = Asset.objects.create(
                asset_type=DomainType.EQUITY,
                name=name,
                currency=record.get("currency"),
            )
            AssetIdentifier.objects.create(
                asset=asset,
                id_type=AssetIdentifier.IdentifierType.TICKER,
                value=symbol,
                is_primary=True,
            )
            EquityDetail.objects.create(
                asset=asset,
                exchange=exchange,
                country=record.get("country"),
                listing_status="ACTIVE",
            )

            created_count += 1

        logger.info(f"Seeded {created_count} equities into the universe.")
        return created_count

    @staticmethod
    @transaction.atomic
    def sync_universe() -> dict:
        """
        Sync universe with FMP feed:
        - Add new tickers
        - Mark missing ones as DELISTED
        """
        records = fetch_equity_universe()
        seen_symbols = {r["symbol"] for r in records if r.get("symbol")}

        # Mark missing assets as DELISTED
        existing_ids = AssetIdentifier.objects.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER
        ).select_related("asset")

        for identifier in existing_ids:
            if identifier.value not in seen_symbols:
                detail = getattr(identifier.asset, "equity_detail", None)
                if detail and detail.listing_status != "DELISTED":
                    detail.listing_status = "DELISTED"
                    detail.save()

        # Add new assets
        created = 0
        for record in records:
            symbol = record.get("symbol")
            if not symbol:
                continue

            if not AssetIdentifier.objects.filter(
                id_type=AssetIdentifier.IdentifierType.TICKER, value=symbol
            ).exists():
                asset = Asset.objects.create(
                    asset_type=DomainType.EQUITY,
                    name=record.get("name"),
                    currency=record.get("currency"),
                )
                AssetIdentifier.objects.create(
                    asset=asset,
                    id_type=AssetIdentifier.IdentifierType.TICKER,
                    value=symbol,
                    is_primary=True,
                )
                EquityDetail.objects.create(
                    asset=asset,
                    exchange=record.get("exchangeShortName"),
                    country=record.get("country"),
                    listing_status="ACTIVE",
                )
                created += 1

        logger.info(f"Synced equity universe. Added {created} new equities.")
        return {"created": created}
    
    @staticmethod
    def create_from_symbol(symbol: str) -> Asset:
        """
        Create a new equity asset (Asset + Identifiers + EquityDetail)
        from a ticker symbol. Enriches with profile and quote if available.
        """
        from django.db import transaction

        symbol = symbol.upper().strip()

        # Check if it already exists
        try:
            identifier = AssetIdentifier.objects.get(
                id_type=AssetIdentifier.IdentifierType.TICKER,
                value=symbol,
            )
            return identifier.asset
        except AssetIdentifier.DoesNotExist:
            pass

        profile = fetch_equity_profile(symbol) or {}
        quote = fetch_equity_quote(symbol) or {}

        with transaction.atomic():
            # --- Create Asset ---
            asset = Asset.objects.create(
                asset_type=DomainType.EQUITY,
                name=profile.get("asset__name") or profile.get("companyName") or symbol,
                currency=profile.get("currency"),
            )


            # --- Primary Identifier (Ticker) ---
            AssetIdentifier.objects.create(
                asset=asset,
                id_type=AssetIdentifier.IdentifierType.TICKER,
                value=symbol,
                is_primary=True,
            )

            # --- Additional Identifiers (if available) ---
            extra_ids = {
                AssetIdentifier.IdentifierType.ISIN: profile.get("isin"),
                AssetIdentifier.IdentifierType.CUSIP: profile.get("cusip"),
                AssetIdentifier.IdentifierType.CIK: profile.get("cik"),
                # add FIGI or others if your API returns them
            }
            for id_type, value in extra_ids.items():
                if value:
                    AssetIdentifier.objects.get_or_create(
                        asset=asset,
                        id_type=id_type,
                        value=value,
                        defaults={"is_primary": False},
                    )

            # --- Equity Detail ---
            detail = EquityDetail.objects.create(
                asset=asset,
                exchange=profile.get("exchange") or profile.get("exchangeShortName"),
                country=profile.get("country"),
                listing_status="ACTIVE" if profile else "IPO",
            )

            # Apply profile fields
            for field, value in profile.items():
                if hasattr(detail, field):
                    setattr(detail, field, value)

            # Apply quote fields
            for field, value in quote.items():
                if hasattr(detail, field):
                    setattr(detail, field, value)

            detail.save()

        return asset
