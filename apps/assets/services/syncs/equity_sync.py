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
            isin = asset.identifiers.filter(
                id_type=AssetIdentifier.IdentifierType.ISIN).first()
            if isin:
                profile = search_by_isin(isin.value)

        detail = _get_or_create_detail(asset)
        if not profile:
            logger.warning(f"No profile for {symbol}")
            detail.listing_status = "DELISTED"
            detail.save()
            return False

        # Ticker drift
        profile_symbol = profile.get("symbol")
        if profile_symbol and profile_symbol != symbol:
            logger.info(
                f"Ticker change {symbol} → {profile_symbol} for {asset}")
            AssetIdentifier.objects.filter(
                asset=asset, id_type=AssetIdentifier.IdentifierType.TICKER,
                value=symbol, is_primary=True
            ).update(is_primary=False)
            _upsert_identifier(
                asset, AssetIdentifier.IdentifierType.TICKER, profile_symbol, True)

        # Company name drift
        if profile.get("companyName") and profile["companyName"] != asset.name:
            asset.name = profile["companyName"]
            asset.is_custom = False
            asset.save()

        _apply_fields(detail, profile)
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
                        id_type=AssetIdentifier.IdentifierType.TICKER, value=symbol
                    ).select_related("asset").first()
                    if not identifier:
                        continue
                    detail = _get_or_create_detail(identifier.asset)
                    _apply_fields(detail, record)
                    detail.is_custom = False
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
    def sync_universe() -> dict:
        records = fetch_equity_universe()
        seen = {r["symbol"] for r in records if r.get("symbol")}
        existing = AssetIdentifier.objects.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER
        ).select_related("asset")

        created, delisted, upgraded = 0, 0, 0

        # Delist missing
        for identifier in existing:
            if identifier.asset.is_custom:
                continue
            if identifier.value not in seen:
                detail = getattr(identifier.asset, "equity_detail", None)
                if detail and detail.listing_status != "DELISTED":
                    detail.listing_status = "DELISTED"
                    detail.save()
                    delisted += 1

        # Add / Upgrade
        for r in records:
            symbol = r.get("symbol")
            if not symbol:
                continue
            identifier = AssetIdentifier.objects.filter(
                id_type=AssetIdentifier.IdentifierType.TICKER, value=symbol
            ).select_related("asset").first()

            if identifier:
                asset = identifier.asset
                if asset.is_custom:
                    asset.is_custom = False
                    asset.name = r.get("name") or r.get(
                        "companyName") or symbol
                    asset.currency = r.get(
                        "currency") or asset.currency or "USD"
                    asset.save()
                    detail = _get_or_create_detail(asset)
                    detail.exchange = r.get(
                        "exchangeShortName") or r.get("exchange")
                    detail.country = r.get("country")
                    detail.listing_status = "ACTIVE"
                    detail.save()
                    upgraded += 1
                continue

            # Create new
            asset = Asset.objects.create(
                asset_type=DomainType.EQUITY,
                name=r.get("name") or r.get("companyName") or symbol,
                currency=r.get("currency"),
                is_custom=False,
            )
            _upsert_identifier(
                asset, AssetIdentifier.IdentifierType.TICKER, symbol, True)
            EquityDetail.objects.create(
                asset=asset,
                exchange=r.get("exchangeShortName") or r.get("exchange"),
                country=r.get("country"),
                listing_status="ACTIVE",
            )
            created += 1

        logger.info(
            f"Universe sync: +{created}, upgraded {upgraded}, delisted {delisted}")
        return {"created": created, "upgraded": upgraded, "delisted": delisted}

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
