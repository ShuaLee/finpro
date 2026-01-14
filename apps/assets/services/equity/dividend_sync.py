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

    Forward dividend logic:
    - Average of regular dividends paid in trailing 12 months
    - Projected forward using most recent regular frequency
    """

    @transaction.atomic
    def sync(self, asset: Asset) -> None:
        if asset.asset_type.slug != "equity":
            return

        ticker = asset.equity.ticker
        events = FMP_PROVIDER.get_equity_dividends(ticker)

        # --------------------------------------------------
        # No dividends at all
        # --------------------------------------------------
        if not events:
            EquityDividendSnapshot.objects.update_or_create(
                asset=asset,
                defaults={
                    "status": EquityDividendSnapshot.DividendStatus.INACTIVE,
                    "cadence_status": EquityDividendSnapshot.DividendCadenceStatus.NONE,
                    "trailing_12m_dividend": Decimal("0"),
                    "trailing_12m_cashflow": Decimal("0"),
                    "forward_annual_dividend": None,
                },
            )
            return

        # --------------------------------------------------
        # Sort newest → oldest
        # --------------------------------------------------
        events.sort(key=lambda e: e.get("date"), reverse=True)

        now = timezone.now().date()
        cutoff = now - datetime.timedelta(days=365)

        trailing_regular = Decimal("0")
        trailing_cashflow = Decimal("0")
        regular_count = 0

        last_event = events[0]
        last_regular = None

        status = EquityDividendSnapshot.DividendStatus.INACTIVE
        cadence_status = EquityDividendSnapshot.DividendCadenceStatus.NONE
        forward = None

        # --------------------------------------------------
        # Single-pass scan
        # --------------------------------------------------
        for e in events:
            div_date = e.get("date")
            if not div_date or div_date < cutoff:
                break

            dividend = Decimal(str(e.get("dividend") or 0))
            if dividend <= 0:
                continue

            freq = e.get("frequency")
            freq = freq.title() if isinstance(freq, str) else None

            # Cashflow = ALL dividends
            trailing_cashflow += dividend

            # Regular dividends only
            if freq in FREQUENCY_MULTIPLIER:
                trailing_regular += dividend
                regular_count += 1

                if last_regular is None:
                    last_regular = e

        # --------------------------------------------------
        # Forward dividend estimate + cadence health
        # --------------------------------------------------
        if last_regular and regular_count > 0:
            freq = last_regular.get("frequency")
            freq = freq.title() if isinstance(freq, str) else None

            multiplier = FREQUENCY_MULTIPLIER.get(freq)
            grace = FREQUENCY_GRACE_DAYS.get(freq)
            last_date = last_regular.get("date")

            if multiplier and grace and last_date:
                days_since = (now - last_date).days

                if days_since <= grace:
                    avg_dividend = trailing_regular / Decimal(regular_count)
                    forward = avg_dividend * multiplier

                    cadence_status = (
                        EquityDividendSnapshot.DividendCadenceStatus.ACTIVE
                    )
                    status = EquityDividendSnapshot.DividendStatus.CONFIDENT

                else:
                    cadence_status = (
                        EquityDividendSnapshot.DividendCadenceStatus.STALE
                    )
                    status = EquityDividendSnapshot.DividendStatus.UNCERTAIN

            else:
                cadence_status = (
                    EquityDividendSnapshot.DividendCadenceStatus.BROKEN
                )
                status = EquityDividendSnapshot.DividendStatus.UNCERTAIN

        else:
            cadence_status = EquityDividendSnapshot.DividendCadenceStatus.NONE
            status = EquityDividendSnapshot.DividendStatus.INACTIVE

        # --------------------------------------------------
        # Persist snapshot
        # --------------------------------------------------
        EquityDividendSnapshot.objects.update_or_create(
            asset=asset,
            defaults={
                # Last actual dividend (fact)
                "last_dividend_amount": Decimal(
                    str(last_event.get("dividend") or 0)
                ),
                "last_dividend_date": last_event.get("date"),
                "last_dividend_frequency": last_event.get("frequency"),
                "last_dividend_is_special": (
                    last_event.get("frequency") not in FREQUENCY_MULTIPLIER
                ),

                # Regular anchor (inference)
                "regular_dividend_amount": (
                    Decimal(str(last_regular.get("dividend")))
                    if last_regular else None
                ),
                "regular_dividend_date": (
                    last_regular.get("date") if last_regular else None
                ),
                "regular_dividend_frequency": (
                    last_regular.get("frequency") if last_regular else None
                ),

                # Trailing (facts)
                "trailing_12m_dividend": trailing_regular,
                "trailing_12m_cashflow": trailing_cashflow,

                # Forward (heuristic)
                "forward_annual_dividend": forward,

                # Health & confidence
                "cadence_status": cadence_status,
                "status": status,
            },
        )
