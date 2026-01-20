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
    """
    Filter out Special / Irregular and zero dividends.
    Assumes events are sorted newest → oldest.
    """
    return [
        e for e in events
        if e.get("frequency", "").title() in FREQUENCY_MULTIPLIER
        and Decimal(str(e.get("dividend") or 0)) > 0
    ]


def calculate_trailing_stock_dividend(events, today):
    """
    Stock trailing:
    - Prefer last N regular payments of active frequency
    - Fallback to last 365 days
    """
    if not events:
        return Decimal("0")

    events = sorted(events, key=lambda e: e["date"], reverse=True)
    cutoff = today - datetime.timedelta(days=365)

    regular = _regular_dividends(events)
    if not regular:
        return Decimal("0")

    freq = regular[0]["frequency"].title()
    required = FREQUENCY_MULTIPLIER[freq]

    same_freq = [
        e for e in regular
        if e["frequency"].title() == freq
    ]

    # Preferred: last N payments
    if len(same_freq) >= required:
        return sum(
            Decimal(str(e["dividend"])) for e in same_freq[:required]
        )

    # Fallback: 12-month window
    trailing = Decimal("0")
    for e in same_freq:
        if e["date"] >= cutoff:
            trailing += Decimal(str(e["dividend"]))

    return trailing


def calculate_trailing_etf_dividend(events):
    """
    ETF trailing:
    - Always sum exactly last N regular payments
    - Never use time windows
    """
    if not events:
        return Decimal("0")

    events = sorted(events, key=lambda e: e["date"], reverse=True)
    regular = _regular_dividends(events)

    if not regular:
        return Decimal("0")

    freq = regular[0]["frequency"].title()
    required = FREQUENCY_MULTIPLIER[freq]

    return sum(
        Decimal(str(e["dividend"])) for e in regular[:required]
    )


def calculate_forward_dividend(events):
    """
    Simple forward:
    - Active frequency only
    - Run-rate if last two equal
    - Else average × N
    """
    if not events:
        return None

    events = sorted(events, key=lambda e: e["date"], reverse=True)
    regular = _regular_dividends(events)

    if len(regular) < 2:
        return None

    freq = regular[0]["frequency"].title()
    required = FREQUENCY_MULTIPLIER[freq]

    same_freq = [
        e for e in regular
        if e["frequency"].title() == freq
    ]

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

        if not events:
            EquityDividendSnapshot.objects.update_or_create(
                asset=asset,
                defaults={
                    "trailing_12m_dividend": Decimal("0"),
                    "trailing_12m_cashflow": Decimal("0"),
                    "forward_annual_dividend": None,
                    "status": EquityDividendSnapshot.DividendStatus.INACTIVE,
                    "cadence_status": EquityDividendSnapshot.DividendCadenceStatus.NONE,
                },
            )
            return

        events.sort(key=lambda e: e["date"], reverse=True)
        last_event = events[0]

        # ---------------- ETF ----------------
        if equity.is_etf:
            trailing = calculate_trailing_etf_dividend(events)

            EquityDividendSnapshot.objects.update_or_create(
                asset=asset,
                defaults={
                    "last_dividend_amount": Decimal(str(last_event["dividend"])),
                    "last_dividend_date": last_event["date"],
                    "last_dividend_frequency": last_event.get("frequency"),
                    "last_dividend_is_special": True,

                    "regular_dividend_amount": None,
                    "regular_dividend_date": None,
                    "regular_dividend_frequency": None,

                    "trailing_12m_dividend": trailing,
                    "trailing_12m_cashflow": trailing,
                    "forward_annual_dividend": None,

                    "status": EquityDividendSnapshot.DividendStatus.CONFIDENT,
                    "cadence_status": EquityDividendSnapshot.DividendCadenceStatus.NONE,
                },
            )
            return

        # ---------------- STOCK ----------------

        trailing_regular = calculate_trailing_stock_dividend(events, now)
        forward = calculate_forward_dividend(events)

        trailing_cashflow = Decimal("0")
        for e in events:
            if e["date"] < cutoff:
                break
            trailing_cashflow += Decimal(str(e.get("dividend") or 0))

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

                "trailing_12m_dividend": trailing_regular,
                "trailing_12m_cashflow": trailing_cashflow,
                "forward_annual_dividend": forward,

                "status": EquityDividendSnapshot.DividendStatus.CONFIDENT,
                "cadence_status": (
                    EquityDividendSnapshot.DividendCadenceStatus.ACTIVE
                    if forward else EquityDividendSnapshot.DividendCadenceStatus.BROKEN
                ),
            },
        )

        SCVRefreshService.asset_changed(asset)
