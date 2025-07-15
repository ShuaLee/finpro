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
    return account


def create_managed_account(user, data):
    """
    Create a Managed Stock Account for the user's StockPortfolio.
    """
    stock_portfolio = _get_user_stock_portfolio(user)

    # Default currency from profile if not provided
    if 'currency' not in data:
        data['currency'] = user.profile.preferred_currency

    account = ManagedAccount.objects.create(
        stock_portfolio=stock_portfolio,
        **data
    )
    return account


def _get_user_stock_portfolio(user):
    """
    Ensure the user has a StockPortfolio.
    """
    if not hasattr(user.profile.portfolio, 'stockportfolio'):
        raise ValidationError("Stock portfolio does not exist for this user.")
    return user.profile.portfolio.stockportfolio