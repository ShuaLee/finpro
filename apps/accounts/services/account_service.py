from django.db import transaction
from django.core.exceptions import ValidationError
from accounts.models.account import Account, AccountType
from accounts.models.details import (
    StockSelfManagedDetails,
    StockManagedDetails,
    CustomAccountDetails,
)


class AccountService:
    """
    Service layer for managing accounts across all subportfolios.
    """

    @staticmethod
    @transaction.atomic
    def create_account(subportfolio, name: str, account_type: str, currency: str = "USD", **details):
        """
        Create a new account and its detail record if needed.

        Args:
            subportfolio (SubPortfolio): The parent subportfolio.
            name (str): Account name.
            account_type (str): One of AccountType.*.
            currency (str): Account currency.
            details (dict): Extra fields for detail models.

        Returns:
            Account
        """
        # Ensure type is valid for this subportfolio
        cfg = subportfolio.get_config()
        if account_type not in cfg.get("account_types", []):
            raise ValidationError(f"{account_type} not allowed in {subportfolio.type} subportfolio")

        account = Account.objects.create(
            subportfolio=subportfolio,
            name=name,
            type=account_type,
            currency=currency,
        )

        # Create details if required
        if account_type == AccountType.STOCK_SELF_MANAGED:
            StockSelfManagedDetails.objects.create(account=account, **details)
        elif account_type == AccountType.STOCK_MANAGED:
            StockManagedDetails.objects.create(account=account, **details)
        elif account_type == AccountType.CUSTOM:
            CustomAccountDetails.objects.create(account=account, **details)

        return account

    @staticmethod
    @transaction.atomic
    def delete_account(account: Account):
        """
        Delete an account and its related detail + holdings.
        """
        # Delete detail model if exists
        if hasattr(account, "stock_self_details"):
            account.stock_self_details.delete()
        if hasattr(account, "stock_managed_details"):
            account.stock_managed_details.delete()
        if hasattr(account, "custom_details"):
            account.custom_details.delete()

        # Delete holdings (if any)
        if hasattr(account, "holdings"):
            account.holdings.all().delete()

        account.delete()

    @staticmethod
    def get_total_value(account: Account):
        """
        Compute total value for an account (varies by type).
        """
        if account.type == AccountType.STOCK_SELF_MANAGED:
            total = 0
            for holding in account.holdings.all():
                val = holding.get_current_value()
                if val:
                    total += val
            return total

        elif account.type == AccountType.STOCK_MANAGED:
            return account.stock_managed_details.current_value

        elif account.type == AccountType.CRYPTO_WALLET:
            total = 0
            for holding in account.holdings.all():
                val = holding.get_current_value()
                if val:
                    total += val
            return total

        elif account.type == AccountType.METAL_STORAGE:
            total = 0
            for holding in account.holdings.all():
                val = holding.get_current_value()
                if val:
                    total += val
            return total

        elif account.type == AccountType.CUSTOM:
            # Could roll up recursively if hierarchical
            return sum(h.get_current_value() for h in account.holdings.all())

        return 0
