from decimal import Decimal
from typing import Iterable

from assets.models.events import EquityDividendEvent
from assets.services.dividends.frequency import frequency_multiplier
from assets.services.dividends.selectors import (
    events_last_n_months,
    most_recent_event,
)


def trailing_dividend_12m(
    events: Iterable[EquityDividendEvent],
) -> Decimal | None:
    """
    Compute trailing 12-month dividend using ex-date.

    Includes ALL dividends paid within the window.
    No special dividend filtering is applied.
    """
    recent = events_last_n_months(events, months=12)

    if not recent:
        return None

    return sum((e.dividend for e in recent), Decimal("0"))


def forward_dividend(
    events: Iterable[EquityDividendEvent],
) -> Decimal | None:
    """
    Compute a naive forward dividend projection based on
    the most recent dividend event and its frequency.

    Returns None if:
    - no events exist
    - frequency is unknown or unsupported
    """
    latest = most_recent_event(events)
    if not latest:
        return None

    multiplier = frequency_multiplier(latest.frequency)
    if not multiplier:
        return None

    return latest.dividend * Decimal(multiplier)
