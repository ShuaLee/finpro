from accounts.models import SelfManagedAccount, ManagedAccount

def get_stock_accounts_dashboard(user):
    """
    Return dashboard summary for all stock accounts of the user.
    """
    stock_portfolio = user.profile.portfolio.stockportfolio
    data = {
        "total_self_managed_value_fx": 0.0,
        "total_managed_value_fx": 0.0,
        "combined_total_fx": 0.0,
        "self_managed_accounts": [],
        "managed_accounts": []
    }

    # Self-managed accounts
    for account in SelfManagedAccount.objects.filter(stock_portfolio=stock_portfolio):
        value = float(account.get_current_value_profile_fx() or 0)
        data["total_self_managed_value_fx"] += value
        data["self_managed_accounts"].append({
            "id": account.id,
            "name": account.name,
            "current_value_fx": value
        })

    # Managed accounts
    for account in ManagedAccount.objects.filter(stock_portfolio=stock_portfolio):
        value = float(account.get_current_value_in_profile_fx() or 0)
        data["total_managed_value_fx"] += value
        data["managed_accounts"].append({
            "id": account.id,
            "name": account.name,
            "current_value_fx": value
        })

    data["combined_total_fx"] = round(
        data["total_self_managed_value_fx"] + data["total_managed_value_fx"], 2
    )
    return data