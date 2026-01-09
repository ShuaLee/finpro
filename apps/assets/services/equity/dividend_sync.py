import datetime
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from assets.models.core import Asset
from assets.models.equity import EquityDividendSnapshot
from external_data.providers.fmp.client import FMP_PROVIDER


FREQUENCY_MULTIPLIER = {
    "Quarterly": 4,
    "Semi-Annual": 2,
    "Annual": 1,
}

FREQUENCY_GRACE_DAYS = {
    "Quarterly": 120,
    "Semi-Annual": 210,
    "Annual": 420,
}


class EquityDividendSyncService:
    """
    Rebuilds the dividend snapshot for an equity asset.

    Optimized:
    - Single sort
    - Single pass
    - Early cutoff
    """

    @transaction.atomic
    def sync(self, asset: Asset) -> None:
        if asset.asset_type.slug != "equity":
            return

        ticker = asset.equity.ticker
        events = FMP_PROVIDER.get_equity_dividends(ticker)

        if not events:
            EquityDividendSnapshot.objects.update_or_create(
                asset=asset,
                defaults={
                    "status": EquityDividendSnapshot.DividendStatus.INACTIVE,
                    "trailing_12m_dividend": Decimal("0"),
                    "trailing_12m_cashflow": Decimal("0"),
                    "forward_annual_dividend": None,
                },
            )
            return

        # --------------------------------------------------
        # Sort newest → oldest
        # --------------------------------------------------
        events.sort(key=lambda e: e["date"], reverse=True)

        now = timezone.now().date()
        cutoff = now - datetime.timedelta(days=365)

        trailing_regular = Decimal("0")
        trailing_cashflow = Decimal("0")

        last_event = events[0]
        last_regular = None

        status = EquityDividendSnapshot.DividendStatus.INACTIVE
        forward = None

        # --------------------------------------------------
        # Single-pass scan
        # --------------------------------------------------
        for e in events:
            div_date = e["date"]
            dividend = Decimal(str(e["dividend"]))
            freq = e.get("frequency")

            if div_date < cutoff:
                break  # 🔥 early exit

            # Cashflow = ALL dividends
            trailing_cashflow += dividend

            # Regular-only logic
            if freq in FREQUENCY_MULTIPLIER:
                trailing_regular += dividend
                if not last_regular:
                    last_regular = e

        # --------------------------------------------------
        # Forward estimate
        # --------------------------------------------------
        if last_regular:
            freq = last_regular["frequency"]
            last_date = last_regular["date"]

            days_since = (now - last_date).days
            grace = FREQUENCY_GRACE_DAYS.get(freq)

            if grace and days_since <= grace:
                forward = (
                    Decimal(str(last_regular["dividend"]))
                    * FREQUENCY_MULTIPLIER[freq]
                )
                status = EquityDividendSnapshot.DividendStatus.CONFIDENT
            else:
                status = EquityDividendSnapshot.DividendStatus.UNCERTAIN

        # --------------------------------------------------
        # Persist snapshot
        # --------------------------------------------------
        EquityDividendSnapshot.objects.update_or_create(
            asset=asset,
            defaults={
                # Last actual dividend
                "last_dividend_amount": last_event["dividend"],
                "last_dividend_date": last_event["date"],
                "last_dividend_frequency": last_event.get("frequency"),
                "last_dividend_is_special": (
                    last_event.get("frequency") not in FREQUENCY_MULTIPLIER
                ),

                # Regular anchor
                "regular_dividend_amount": (
                    last_regular["dividend"] if last_regular else None
                ),
                "regular_dividend_date": (
                    last_regular["date"] if last_regular else None
                ),
                "regular_dividend_frequency": (
                    last_regular["frequency"] if last_regular else None
                ),

                # Computed
                "trailing_12m_dividend": trailing_regular,
                "trailing_12m_cashflow": trailing_cashflow,
                "forward_annual_dividend": forward,
                "status": status,
            },
        )
