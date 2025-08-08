from django.core.exceptions import ValidationError
from accounts.models.stocks import StockAccount


def create_stock_account(user, data):
    """
    Create a StockAccount for the user's StockPortfolio.
    Accepts:
      - name (str)
      - account_mode: "self_managed" | "managed"  (default "self_managed")
      - currency: ISO 4217 code or "profile" (default: profile currency)
      - broker, tax_status, strategy, current_value, invested_amount (optional)
      - stock_portfolio is derived from user
    """
    stock_portfolio = _get_user_stock_portfolio(user)

    mode = data.get("account_mode", "self_managed")
    if mode not in {"self_managed", "managed"}:
        raise ValidationError("Invalid account_mode. Use 'self_managed' or 'managed'.")

    # Normalize currency
    currency = data.get("currency")
    if not currency or (isinstance(currency, str) and currency.lower() == "profile"):
        currency = user.profile.currency  # assuming Profile.currency field
    data["currency"] = currency

    # Scrub managed-only fields if creating a self-managed account
    if mode == "self_managed":
        data["strategy"] = None
        data["current_value"] = None
        data["invested_amount"] = None

    account = StockAccount.objects.create(
        stock_portfolio=stock_portfolio,
        **data
    )

    # Initialize schema visibility for the active schema (derived by mode)
    if account.active_schema:
        account.initialize_visibility_settings(account.active_schema)

    return account


def get_stock_accounts(user, mode=None):
    """
    Return all StockAccount(s) for the user's StockPortfolio.
    Optional filter by mode: "self_managed" | "managed".
    """
    sp = _get_user_stock_portfolio(user)
    qs = StockAccount.objects.filter(stock_portfolio=sp)
    if mode in {"self_managed", "managed"}:
        qs = qs.filter(account_mode=mode)
    return qs


# -------- Backwards-compatible shims (safe to remove once views are migrated) -------- #

def create_self_managed_account(user, data):
    data = {**data, "account_mode": "self_managed"}
    return create_stock_account(user, data)


def create_managed_account(user, data):
    data = {**data, "account_mode": "managed"}
    return create_stock_account(user, data)


def get_self_managed_accounts(user):
    return get_stock_accounts(user, mode="self_managed")


def get_managed_accounts(user):
    return get_stock_accounts(user, mode="managed")


# --------------------------------- internals --------------------------------- #

def _get_user_stock_portfolio(user):
    """
    Resolve user's StockPortfolio or raise a ValidationError.
    """
    portfolio = getattr(user.profile, "portfolio", None)
    if not portfolio or not hasattr(portfolio, 'stockportfolio'):
        raise ValidationError("Stock portfolio does not exist for this user.")
    return portfolio.stockportfolio
