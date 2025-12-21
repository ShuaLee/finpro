from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from assets.models.events.equity import EquityDividendExtension
from assets.services.dividends.calculations import (
    trailing_dividend_12m,
    forward_dividend,
)

YIELD_QUANT = Decimal("0.000001")


def recompute_dividend_extension(asset):
    """
    Recompute all derived dividend metrics for an equity asset.

    Triggered by:
    - dividend event changes
    - price changes

    Safe to call repeatedly.
    """

    events = asset.dividend_events.all()
    if not events.exists():
        return

    extension, _ = EquityDividendExtension.objects.get_or_create(
        asset=asset
    )

    # -----------------------------
    # Dividend amounts
    # -----------------------------
    trailing = trailing_dividend_12m(events)
    forward = forward_dividend(events)

    extension.trailing_dividend_12m = trailing
    extension.forward_dividend = forward

    # -----------------------------
    # Yield calculation (price-aware)
    # -----------------------------
    price = asset.latest_price  # ✅ correct abstraction

    if price and price > 0:
        try:
            extension.trailing_yield = (
                (trailing / price).quantize(YIELD_QUANT, rounding=ROUND_HALF_UP)
                if trailing is not None
                else None
            )
            extension.forward_yield = (
                (forward / price).quantize(YIELD_QUANT, rounding=ROUND_HALF_UP)
                if forward is not None
                else None
            )
        except (InvalidOperation, ZeroDivisionError):
            extension.trailing_yield = None
            extension.forward_yield = None
    else:
        extension.trailing_yield = None
        extension.forward_yield = None

    extension.save()
