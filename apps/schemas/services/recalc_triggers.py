from typing import Iterable
from schemas.services.holding_sync_service import recalc_calculated_for_holding

def _recalc_many(holdings: Iterable):
    for h in holdings:
        recalc_calculated_for_holding(h)

def recalc_holdings_for_profile(profile):
    """
    Recalculate calculated SCVs for all holdings under the given profile.
    Currently handles self-managed stock holdings. Extend for metals/managed as needed.
    """
    # Import inside to avoid import-time cycles
    from assets.models.stocks import StockHolding

    qs = (
        StockHolding.objects
        .filter(self_managed_account__stock_portfolio__portfolio__profile_id=profile.id)  # ✅ correct relation
        .select_related(
            "self_managed_account",
            "self_managed_account__stock_portfolio",
            "self_managed_account__stock_portfolio__portfolio",
            "self_managed_account__stock_portfolio__portfolio__profile",
            "stock",
        )
    )
    _recalc_many(qs)


def recalc_holdings_for_fx_pair(from_currency: str, to_currency: str):
    """
    Recalculate holdings where asset currency == from_currency
    and profile currency == to_currency.
    """
    from assets.models.stocks import StockHolding

    qs = (
        StockHolding.objects
        .filter(
            stock__currency=from_currency,
            self_managed_account__stock_portfolio__portfolio__profile__currency=to_currency,
        )
        .select_related(
            "self_managed_account",
            "self_managed_account__stock_portfolio__portfolio__profile",
            "stock",
        )
    )
    _recalc_many(qs)