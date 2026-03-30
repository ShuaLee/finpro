from django.apps import apps
from django.db import transaction

from accounts.models import Account


class AccountDeletionService:
    """
    Canonical account deletion entry point.
    """

    @staticmethod
    @transaction.atomic
    def delete_account(*, account: Account) -> None:
        portfolio = account.portfolio
        account_type = account.account_type
        account.delete()

        try:
            Schema = apps.get_model("schemas", "Schema")
        except (LookupError, ValueError):
            return

        still_exists = portfolio.accounts.filter(account_type=account_type).exists()
        if not still_exists:
            Schema.objects.filter(
                portfolio=portfolio,
                account_type=account_type,
                asset_type__isnull=True,
            ).delete()
