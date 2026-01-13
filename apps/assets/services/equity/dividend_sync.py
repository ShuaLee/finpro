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

        events.sort(key=lambda e: e["date"], reverse=True)

        now = timezone.now().date()
        cutoff = now - datetime.timedelta(days=365)

        trailing_regular = Decimal("0")
        trailing_cashflow = Decimal("0")

        last_event = events[0]
        last_regular = None

        status = EquityDividendSnapshot.DividendStatus.INACTIVE
        forward = None

        for e in events:
            div_date = e["date"]
            if div_date < cutoff:
                break

            dividend = Decimal(str(e["dividend"]))
            if dividend <= 0:
                continue

            freq = e.get("frequency")
            freq = freq.title() if isinstance(freq, str) else None

            trailing_cashflow += dividend

            if freq in FREQUENCY_MULTIPLIER:
                trailing_regular += dividend
                if last_regular is None:
                    last_regular = e

        if last_regular:
            freq = last_regular["frequency"].title()
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

        EquityDividendSnapshot.objects.update_or_create(
            asset=asset,
            defaults={
                "last_dividend_amount": Decimal(str(last_event["dividend"])),
                "last_dividend_date": last_event["date"],
                "last_dividend_frequency": last_event.get("frequency"),
                "last_dividend_is_special": (
                    last_event.get("frequency") not in FREQUENCY_MULTIPLIER
                ),

                "regular_dividend_amount": (
                    Decimal(str(last_regular["dividend"]))
                    if last_regular else None
                ),
                "regular_dividend_date": (
                    last_regular["date"] if last_regular else None
                ),
                "regular_dividend_frequency": (
                    last_regular["frequency"] if last_regular else None
                ),

                "trailing_12m_dividend": trailing_regular,
                "trailing_12m_cashflow": trailing_cashflow,
                "forward_annual_dividend": forward,
                "status": status,
            },
        )