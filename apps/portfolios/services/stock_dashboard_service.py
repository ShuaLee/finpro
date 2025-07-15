"""
Stock Dashboard Service
-----------------------

Handles business logic for generating a stock portfolio dashboard summary.
"""

from portfolios.models import StockPortfolio
from accounts.models.stocks import ManagedAccount


def get_stock_dashboard(stock_portfolio: StockPortfolio) -> dict:
    """
    Builds a dashboard summary for the given StockPortfolio.

    Args:
        stock_portfolio (StockPortfolio): The user's stock portfolio instance.

    Returns:
        dict: Dashboard data including totals and account details.
    """

    # Self-managed accounts
    self_managed_accounts = []
    total_self_managed_value = 0

    accounts = stock_portfolio.self_managed_accounts.select_related(
        'active_schema'
    ).prefetch_related(
        'holdings__stock',
        'holdings__column_values__column'
    )

    for account in accounts:
        schema = account.active_schema
        if not schema:
            continue

        columns = schema.columns.all()
        holdings_data = []

        for holding in account.holdings.all():
            row = {}
            col_values = {cv.column_id: cv for cv in holding.column_values.all()}
            for col in columns:
                val = col_values.get(col.id)
                row[col.title] = val.get_value() if val else None
            holdings_data.append(row)

        value = float(account.get_current_value_profile_fx() or 0)
        total_self_managed_value += value

        self_managed_accounts.append({
            "account_id": account.id,
            "account_name": account.name,
            "schema_name": schema.name,
            "current_value_fx": round(value, 2),
            "columns": [col.title for col in columns],
            "holdings": holdings_data,
        })

    # Managed accounts
    managed_accounts = ManagedAccount.objects.filter(
        stock_portfolio=stock_portfolio
    ).select_related('stock_portfolio')

    managed_data = []
    total_managed_value = 0

    for acct in managed_accounts:
        value_fx = float(acct.get_total_current_value_in_profile_fx() or 0)
        total_managed_value += value_fx
        managed_data.append({
            "account_id": acct.id,
            "account_name": acct.name,
            "current_value": float(acct.current_value),
            "invested_amount": float(acct.invested_amount),
            "currency": acct.currency,
            "current_value_fx": round(value_fx, 2),
        })

    return {
        "total_self_managed_value_fx": round(total_self_managed_value, 2),
        "total_managed_value_fx": round(total_managed_value, 2),
        "total_combined_value_fx": round(total_self_managed_value + total_managed_value, 2),
        "self_managed_accounts": self_managed_accounts,
        "managed_accounts": managed_data,
    }
