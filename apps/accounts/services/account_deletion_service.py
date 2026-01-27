from django.db import transaction

from accounts.models import Account
from schemas.models import Schema


class AccountDeletionService:
    """
    Canonical account deletion entry point.

    Responsibilities:
    - Delete the account
    - Delete schema if this was the last account of its type
    """

    @staticmethod
    @transaction.atomic
    def delete_account(*, account: Account) -> None:
        portfolio = account.portfolio
        account_type = account.account_type

        # --------------------------------------------------
        # 1. Delete the account (holdings + SCVs cascade)
        # --------------------------------------------------
        account.delete()

        # --------------------------------------------------
        # 2. Check if schema is still needed
        # --------------------------------------------------
        still_exists = portfolio.accounts.filter(
            account_type=account_type
        ).exists()

        if not still_exists:
            Schema.objects.filter(
                portfolio=portfolio,
                account_type=account_type,
            ).delete()
