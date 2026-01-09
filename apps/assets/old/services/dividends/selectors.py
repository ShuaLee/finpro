from datetime import date, timedelta
from typing import Iterable

from django.utils.timezone import now

from assets.models.events import EquityDividendEvent


def events_last_n_months(
    events: Iterable[EquityDividendEvent],
    months: int,
    as_of: date | None = None,
) -> list[EquityDividendEvent]:
    """
    Return dividend events within the last N months,
    based on ex-date.

    Uses a rolling day-based window (365 * months/12).
    """
    if not as_of:
        as_of = now().date()

    cutoff = as_of - timedelta(days=int(365 * (months / 12)))

    return [
        e for e in events
        if e.ex_date and e.ex_date >= cutoff
    ]


def most_recent_event(
    events: Iterable[EquityDividendEvent],
) -> EquityDividendEvent | None:
    """
    Return the most recent dividend event by ex-date.
    """
    return max(events, key=lambda e: e.ex_date, default=None)
