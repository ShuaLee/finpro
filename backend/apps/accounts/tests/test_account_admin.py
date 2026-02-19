from uuid import uuid4

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import (
    Account,
    AccountClassification,
    AccountType,
    ClassificationDefinition,
)
from accounts.services.account_service import AccountService
from assets.models.core import AssetType
from fx.models.country import Country
from fx.models.fx import FXCurrency
from portfolios.models import Portfolio
from profiles.services.bootstrap_service import ProfileBootstrapService
from subscriptions.models import Plan
from users.models import User


class AccountWorkflowTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="accounts@example.com",
            password="testpass123",
        )
        FXCurrency.objects.get_or_create(
            code="USD",
            defaults={"name": "US Dollar", "is_active": True},
        )
        Country.objects.get_or_create(
            code="US",
            defaults={"name": "United States", "is_active": True},
        )
        Plan.objects.get_or_create(
            slug="free",
            defaults={
                "name": "Free",
                "tier": Plan.Tier.FREE,
                "is_active": True,
            },
        )
        ProfileBootstrapService.bootstrap(user=self.user)
        self.profile = self.user.profile
        self.portfolio = Portfolio.objects.get(
            profile=self.profile,
            kind=Portfolio.Kind.PERSONAL,
        )

        token = uuid4().hex[:8]

        self.asset_type = AssetType.objects.create(
            name=f"System Asset {token}",
        )
        self.account_type = AccountType.objects.create(
            name=f"Brokerage {token}",
            slug=f"brokerage-{token}",
            is_system=True,
        )
        self.account_type.allowed_asset_types.add(self.asset_type)

        self.definition = ClassificationDefinition.objects.create(
            name=f"Taxable {token}",
            tax_status="taxable",
            all_countries=True,
            is_system=True,
        )

    def test_initialize_account_assigns_classification(self):
        account = Account.objects.create(
            portfolio=self.portfolio,
            name="Main Brokerage",
            account_type=self.account_type,
        )

        AccountService.initialize_account(account=account, definition=self.definition)

        account.refresh_from_db()
        self.assertIsNotNone(account.classification)
        self.assertEqual(account.classification.definition, self.definition)

    def test_initialize_account_is_idempotent(self):
        account = Account.objects.create(
            portfolio=self.portfolio,
            name="Long-Term Brokerage",
            account_type=self.account_type,
        )

        AccountService.initialize_account(account=account, definition=self.definition)
        first_classification_id = account.classification_id

        AccountService.initialize_account(account=account, definition=self.definition)
        account.refresh_from_db()

        self.assertEqual(account.classification_id, first_classification_id)
        self.assertEqual(
            AccountClassification.objects.filter(
                profile=self.profile,
                definition=self.definition,
            ).count(),
            1,
        )

    def test_unique_account_name_per_portfolio_type(self):
        Account.objects.create(
            portfolio=self.portfolio,
            name="Duplicate Name",
            account_type=self.account_type,
        )

        with self.assertRaises(ValidationError):
            Account.objects.create(
                portfolio=self.portfolio,
                name="Duplicate Name",
                account_type=self.account_type,
            )

    def test_account_active_schema_none_when_schemas_not_enabled(self):
        account = Account.objects.create(
            portfolio=self.portfolio,
            name="Schema Optional Account",
            account_type=self.account_type,
        )
        self.assertIsNone(account.active_schema)

    def test_custom_account_type_requires_owner(self):
        custom_type = AccountType(name="My Type", is_system=False, owner=None)
        with self.assertRaises(ValidationError):
            custom_type.full_clean()
