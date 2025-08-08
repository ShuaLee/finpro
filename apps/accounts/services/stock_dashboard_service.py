from decimal import Decimal
from accounts.models.stocks import StockAccount


def _to_float(val):
    if val is None:
        return 0.0
    if isinstance(val, Decimal):
        return float(val)
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def get_stock_accounts_dashboard(user):
    """
    Return dashboard summary for all stock accounts of the user.
    Groups by mode and returns per-account value in profile FX,
    plus subtotals and a combined total.
    """
    stock_portfolio = user.profile.portfolio.stockportfolio

    data = {
        "total_self_managed_value_fx": 0.0,
        "total_managed_value_fx": 0.0,
        "combined_total_fx": 0.0,
        "self_managed_accounts": [],
        "managed_accounts": [],
    }

    # Self-managed accounts
    for account in (
        StockAccount.objects
        .filter(stock_portfolio=stock_portfolio, account_mode="self_managed")
        .select_related("stock_portfolio", "stock_portfolio__portfolio__profile")
    ):
        # Uses model helper to compute value in profile currency
        value = _to_float(account.get_value_in_profile_currency())
        data["total_self_managed_value_fx"] += value
        data["self_managed_accounts"].append({
            "id": account.id,
            "name": account.name,
            "current_value_fx": value,
        })

    # Managed accounts
    for account in (
        StockAccount.objects
        .filter(stock_portfolio=stock_portfolio, account_mode="managed")
        .select_related("stock_portfolio", "stock_portfolio__portfolio__profile")
    ):
        value = _to_float(account.get_value_in_profile_currency())
        data["total_managed_value_fx"] += value
        data["managed_accounts"].append({
            "id": account.id,
            "name": account.name,
            "current_value_fx": value,
        })

    data["combined_total_fx"] = round(
        data["total_self_managed_value_fx"] + data["total_managed_value_fx"], 2
    )

    return data
