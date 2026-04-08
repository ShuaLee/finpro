import datetime
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.assets.models import Asset, AssetDividendSnapshot
from apps.assets.services.asset_price_service import AssetPriceService
from apps.integrations.providers.fmp import FMP_PROVIDER


FREQUENCY_MULTIPLIER = {
    "Monthly": 12,
    "Quarterly": 4,
    "Semi-Annual": 2,
    "Annual": 1,
}


def _parse_event_date(raw_value):
    if isinstance(raw_value, datetime.date):
        return raw_value
    if not raw_value:
        return None
    try:
        return datetime.date.fromisoformat(str(raw_value))
    except ValueError:
        return None


def _to_decimal(value):
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _normalize_events(events: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    for event in events or []:
        date = _parse_event_date(event.get("date") or event.get("recordDate") or event.get("paymentDate"))
        amount = _to_decimal(event.get("dividend"))
        if date is None or amount is None:
            continue
        normalized.append(
            {
                "date": date,
                "dividend": amount,
                "frequency": (event.get("frequency") or "").title(),
            }
        )
    normalized.sort(key=lambda item: item["date"], reverse=True)
    return normalized


def _regular_dividends(events):
    return [
        event
        for event in events
        if event.get("frequency") in FREQUENCY_MULTIPLIER and (event.get("dividend") or Decimal("0")) > 0
    ]


def calculate_trailing_dividend(events, today):
    if not events:
        return Decimal("0")

    cutoff = today - datetime.timedelta(days=365)
    regular = _regular_dividends(events)
    if not regular:
        return Decimal("0")

    frequency = regular[0]["frequency"]
    required = FREQUENCY_MULTIPLIER[frequency]
    same_frequency = [event for event in regular if event["frequency"] == frequency]

    if len(same_frequency) >= required:
        return sum((event["dividend"] for event in same_frequency[:required]), Decimal("0"))

    trailing = Decimal("0")
    for event in same_frequency:
        if event["date"] >= cutoff:
            trailing += event["dividend"]
    return trailing


def calculate_forward_dividend(events):
    regular = _regular_dividends(events)
    if len(regular) < 2:
        return None

    frequency = regular[0]["frequency"]
    required = FREQUENCY_MULTIPLIER[frequency]
    same_frequency = [event for event in regular if event["frequency"] == frequency]
    amounts = [event["dividend"] for event in same_frequency[:required]]

    if len(amounts) >= 2 and amounts[0] == amounts[1]:
        return amounts[0] * Decimal(required)

    if not amounts:
        return None

    return (sum(amounts, Decimal("0")) / Decimal(len(amounts))) * Decimal(required)


class AssetDividendService:
    @staticmethod
    def supports_dividends(*, asset: Asset) -> bool:
        return asset.owner is None and asset.asset_type.slug == "equity"

    @staticmethod
    @transaction.atomic
    def sync(asset: Asset) -> AssetDividendSnapshot | None:
        if not AssetDividendService.supports_dividends(asset=asset):
            return None

        symbol = (getattr(getattr(asset, "market_data", None), "provider_symbol", "") or asset.symbol or "").strip().upper()
        if not symbol:
            return None

        raw_events = FMP_PROVIDER.get_dividends(symbol)
        events = _normalize_events(raw_events)
        today = timezone.now().date()
        cutoff = today - datetime.timedelta(days=365)

        snapshot_defaults: dict = {}

        if not events:
            snapshot_defaults = {
                "last_dividend_amount": None,
                "last_dividend_date": None,
                "last_dividend_frequency": None,
                "last_dividend_is_special": False,
                "regular_dividend_amount": None,
                "regular_dividend_date": None,
                "regular_dividend_frequency": None,
                "trailing_12m_dividend": Decimal("0"),
                "trailing_12m_cashflow": Decimal("0"),
                "forward_annual_dividend": None,
                "trailing_dividend_yield": None,
                "forward_dividend_yield": None,
                "status": AssetDividendSnapshot.DividendStatus.INACTIVE,
                "cadence_status": AssetDividendSnapshot.CadenceStatus.NONE,
            }
            snapshot, _ = AssetDividendSnapshot.objects.update_or_create(
                asset=asset,
                defaults=snapshot_defaults,
            )
            return snapshot

        last_event = events[0]
        regular = _regular_dividends(events)
        trailing = calculate_trailing_dividend(events, today)
        forward = calculate_forward_dividend(events)

        trailing_cashflow = Decimal("0")
        for event in events:
            if event["date"] < cutoff:
                break
            trailing_cashflow += event["dividend"]

        trailing_yield = None
        forward_yield = None
        price = None
        try:
            price = AssetPriceService.get_current_price(asset=asset).price
        except Exception:
            price = getattr(getattr(asset, "price", None), "price", None)

        if price and price > 0:
            trailing_yield = trailing / price
            if forward is not None:
                forward_yield = forward / price

        last_is_special = last_event.get("frequency", "") not in FREQUENCY_MULTIPLIER
        cadence_status = (
            AssetDividendSnapshot.CadenceStatus.ACTIVE
            if forward is not None
            else AssetDividendSnapshot.CadenceStatus.BROKEN
        )
        status = (
            AssetDividendSnapshot.DividendStatus.CONFIDENT
            if forward is not None
            else AssetDividendSnapshot.DividendStatus.UNCERTAIN
        )

        snapshot_defaults = {
            "last_dividend_amount": last_event["dividend"],
            "last_dividend_date": last_event["date"],
            "last_dividend_frequency": last_event.get("frequency") or None,
            "last_dividend_is_special": last_is_special,
            "regular_dividend_amount": regular[0]["dividend"] if regular else None,
            "regular_dividend_date": regular[0]["date"] if regular else None,
            "regular_dividend_frequency": regular[0]["frequency"] if regular else None,
            "trailing_12m_dividend": trailing,
            "trailing_12m_cashflow": trailing_cashflow,
            "forward_annual_dividend": forward,
            "trailing_dividend_yield": trailing_yield,
            "forward_dividend_yield": forward_yield,
            "status": status,
            "cadence_status": cadence_status,
        }
        snapshot, _ = AssetDividendSnapshot.objects.update_or_create(
            asset=asset,
            defaults=snapshot_defaults,
        )
        return snapshot

    @staticmethod
    def sync_assets(*, assets) -> dict:
        synced = 0
        inactive = 0
        errors = 0
        for asset in assets:
            try:
                snapshot = AssetDividendService.sync(asset)
                if snapshot is None:
                    continue
                if snapshot.status == AssetDividendSnapshot.DividendStatus.INACTIVE:
                    inactive += 1
                else:
                    synced += 1
            except Exception:
                errors += 1

        return {
            "synced": synced,
            "inactive": inactive,
            "errors": errors,
        }
