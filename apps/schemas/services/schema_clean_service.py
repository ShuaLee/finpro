from schemas.models import Schema


class SchemaCleanupService:
    """
    Handles schema lifecycle when accounts are deleted.
    """

    @staticmethod
    def account_deleted(account):
        """
        Delete schema if this was the last account
        of its type in the portfolio.
        """
        portfolio = account.portfolio
        account_type = account.account_type

        still_exists = portfolio.accounts.filter(
            account_type=account_type
        ).exists()

        if not still_exists:
            Schema.objects.filter(
                portfolio=portfolio,
                account_type=account_type,
            ).delete()
