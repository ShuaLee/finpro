from django.core.exceptions import ValidationError
from accounts.models import SelfManagedAccount, ManagedAccount


def create_self_managed_account(user, data):
    """
    Create a Self-Managed Stock Account for the user's StockPortfolio.
    """
    stock_portfolio = _get_user_stock_portfolio(user)

    account = SelfManagedAccount.objects.create(
        stock_portfolio=stock_portfolio,
        **data
    )

    # Initialize schema visibility
    if account.active_schema:
        account.initialize_visibility_settings(account.active_schema)

    return account


def create_managed_account(user, data):
    """
    Create a Managed Stock Account for the user's StockPortfolio.
    """
    stock_portfolio = _get_user_stock_portfolio(user)

    if 'currency' not in data:
        data['currency'] = user.profile.preferred_currency

    account = ManagedAccount.objects.create(
        stock_portfolio=stock_portfolio,
        **data
    )

    if account.active_schema:
        account.initialize_visibility_settings(account.active_schema)

    return account


def get_self_managed_accounts(user):
    return SelfManagedAccount.objects.filter(
        stock_portfolio=_get_user_stock_portfolio(user)
    )


def get_managed_accounts(user):
    return ManagedAccount.objects.filter(
        stock_portfolio=_get_user_stock_portfolio(user)
    )


def _get_user_stock_portfolio(user):
    """
    Resolve user's stock portfolio or raise error.
    """
    portfolio = getattr(user.profile, "portfolio", None)
    if not hasattr(portfolio, 'stockportfolio'):
        raise ValidationError("Stock portfolio does not exist for this user.")
    return portfolio.stockportfolio
