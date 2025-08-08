from django.core.exceptions import ValidationError


def switch_account_mode(account, new_mode, force=False):
    if new_mode not in ["self_managed", "managed"]:
        raise ValidationError("Invalid account mode")

    if account.account_mode == new_mode:
        return  # No-op

    # Safeguards
    if new_mode == "managed":
        if account.holdings.exists() and not force:
            raise ValidationError(
                "Delete holdings before switching to managed.")
        account.holdings.all().delete()

    if new_mode == "self_managed":
        if account.column_values.exists() and not force:
            raise ValidationError(
                "Clear analytics data before switching to self-managed.")
        account.column_values.all().delete()
        account.current_value = None
        account.invested_amount = None
        account.strategy = None

    account.account_mode = new_mode
    account.save()

    # Re-initialize visibility for new schema
    if account.active_schema:
        account.initialize_visibility_settings(account.active_schema)
