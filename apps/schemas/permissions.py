def is_schema_owner(user, schema):
    return schema.portfolio.profile.user == user


def is_holding_owner(user, holding):
    """
    Works for all account types as long as `account.sub_portfolio.portfolio` pattern holds.
    """
    try:
        return holding.account.sub_portfolio.portfolio.profile.user == user
    except AttributeError:
        return False