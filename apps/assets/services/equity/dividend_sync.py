import datetime
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from assets.models.core import Asset
from assets.models.equity import EquityDividendSnapshot
from external_data.providers.fmp.client import FMP_PROVIDER
from schemas.services.scv_refresh_service import SCVRefreshService


# ============================================================
# Constants
# ============================================================

FREQUENCY_MULTIPLIER = {
    "Monthly": 12,
    "Quarterly": 4,
    "Semi-Annual": 2,
    "Annual": 1,
}


# ============================================================
# Core calculations
# ============================================================

def _regular_dividends(events):
    return [
        e for e in events
        if e.get("frequency", "").title() in FREQUENCY_MULTIPLIER
        and Decimal(str(e.get("dividend") or 0)) > 0
    ]


def calculate_trailing_dividend(events, today):
    if not events:
        return Decimal("0")

    events = sorted(events, key=lambda e: e["date"], reverse=True)
    cutoff = today - datetime.timedelta(days=365)

    regular = _regular_dividends(events)
    if not regular:
        return Decimal("0")

    freq = regular[0]["frequency"].title()
    required = FREQUENCY_MULTIPLIER[freq]

    same_freq = [e for e in regular if e["frequency"].title() == freq]

    if len(same_freq) >= required:
        return sum(Decimal(str(e["dividend"])) for e in same_freq[:required])

    trailing = Decimal("0")
    for e in same_freq:
        if e["date"] >= cutoff:
            trailing += Decimal(str(e["dividend"]))

    return trailing


def calculate_forward_dividend(events):
    if not events:
        return None

    events = sorted(events, key=lambda e: e["date"], reverse=True)
    regular = _regular_dividends(events)
    if len(regular) < 2:
        return None

    freq = regular[0]["frequency"].title()
    required = FREQUENCY_MULTIPLIER[freq]

    same_freq = [e for e in regular if e["frequency"].title() == freq]
    amounts = [Decimal(str(e["dividend"])) for e in same_freq[:required]]

    if len(amounts) >= 2 and amounts[0] == amounts[1]:
        return amounts[0] * Decimal(required)

    return (sum(amounts) / Decimal(len(amounts))) * Decimal(required)


# ============================================================
# Sync Service
# ============================================================

class EquityDividendSyncService:

    @transaction.atomic
    def sync(self, asset: Asset) -> None:
        if asset.asset_type.slug != "equity":
            return

        equity = asset.equity
        events = FMP_PROVIDER.get_equity_dividends(equity.ticker)

        now = timezone.now().date()
        cutoff = now - datetime.timedelta(days=365)

        # --------------------------------------------------
        # Resolve price ONCE
        # --------------------------------------------------
        price_obj = getattr(asset, "price", None)
        price = (
            Decimal(str(price_obj.price))
            if price_obj and price_obj.price and price_obj.price > 0
            else None
        )

        # --------------------------------------------------
        # No dividend data
        # --------------------------------------------------
        if not events:
            EquityDividendSnapshot.objects.update_or_create(
                asset=asset,
                defaults={
                    "trailing_12m_dividend": Decimal("0"),
                    "trailing_12m_cashflow": Decimal("0"),
                    "forward_annual_dividend": None,
                    "trailing_dividend_yield": None,
                    "forward_dividend_yield": None,
                    "status": EquityDividendSnapshot.DividendStatus.INACTIVE,
                    "cadence_status": EquityDividendSnapshot.DividendCadenceStatus.NONE,
                },
            )
            SCVRefreshService.asset_changed(asset)
            return

        events.sort(key=lambda e: e["date"], reverse=True)
        last_event = events[0]

        # --------------------------------------------------
        # Shared calculations (ETF + Stock)
        # --------------------------------------------------
        trailing = calculate_trailing_dividend(events, now)
        forward = calculate_forward_dividend(events)

        trailing_cashflow = Decimal("0")
        for e in events:
            if e["date"] < cutoff:
                break
            trailing_cashflow += Decimal(str(e.get("dividend") or 0))

        trailing_yield = None
        forward_yield = None
        if price:
            trailing_yield = trailing / price
            if forward:
                forward_yield = forward / price

        regular = _regular_dividends(events)

        EquityDividendSnapshot.objects.update_or_create(
            asset=asset,
            defaults={
                "last_dividend_amount": Decimal(str(last_event["dividend"])),
                "last_dividend_date": last_event["date"],
                "last_dividend_frequency": last_event.get("frequency"),
                "last_dividend_is_special": (
                    last_event.get("frequency", "").title()
                    not in FREQUENCY_MULTIPLIER
                ),

                "regular_dividend_amount": (
                    Decimal(str(regular[0]["dividend"])) if regular else None
                ),
                "regular_dividend_date": (
                    regular[0]["date"] if regular else None
                ),
                "regular_dividend_frequency": (
                    regular[0]["frequency"] if regular else None
                ),

                "trailing_12m_dividend": trailing,
                "trailing_12m_cashflow": trailing_cashflow,
                "forward_annual_dividend": forward,

                # ✅ SAME YIELD LOGIC FOR ETF + STOCK
                "trailing_dividend_yield": trailing_yield,
                "forward_dividend_yield": forward_yield,

                "status": EquityDividendSnapshot.DividendStatus.CONFIDENT,
                "cadence_status": (
                    EquityDividendSnapshot.DividendCadenceStatus.ACTIVE
                    if forward else EquityDividendSnapshot.DividendCadenceStatus.BROKEN
                ),
            },
        )

        SCVRefreshService.asset_changed(asset)
