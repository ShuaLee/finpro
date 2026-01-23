from django.db import IntegrityError
from django.test import TestCase

from accounts.models import Account, AccountType, ClassificationDefinition
from accounts.services.account_service import AccountService
from schemas.models import Schema
from users.models import User


class AccountAdminWorkflowTest(TestCase):
    """
    Test proper account creation workflow via admin patterns.

    These tests validate:
    - User/Profile/Portfolio bootstrap
    - Account creation with initialization
    - Schema auto-generation
    - Schema reuse across accounts of same type
    """
    def setUp(self):
        # Create user (triggers bootstrap)
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.profile = self.user.profile
        self.portfolio = self.profile.portfolio

        # Create account type
        self.account_type = AccountType.objects.create(
            name="Brokerage",
            slug="brokerage",
            is_system=True
        )

        # Create classification definition
        self.definition = ClassificationDefinition.objects.create(
            name="TFSA",
            tax_status="tax_exempt",
            all_countries=True,
            is_system=True
        )

    def test_account_creation_with_initialization(self):
        """Test proper account creation flow"""
        # Step 1: Create account
        account = Account.objects.create(
            portfolio=self.portfolio,
            name="My Brokerage",
            account_type=self.account_type,
        )

        # Step 2: Initialize (mimics admin save_model)
        AccountService.initialize_account(
            account=account,
            definition=self.definition
        )

        # Verify classification created
        self.assertIsNotNone(account.classification)
        self.assertEqual(account.classification.definition, self.definition)

        # Verify schema created
        schema = Schema.objects.filter(
            portfolio=self.portfolio,
            account_type=self.account_type
        ).first()
        self.assertIsNotNone(schema)
        self.assertEqual(account.active_schema, schema)

    def test_schema_reused_for_same_account_type(self):
        """Test schema is shared across accounts of same type"""
        # Create first account
        account1 = Account.objects.create(
            portfolio=self.portfolio,
            name="Account 1",
            account_type=self.account_type,
        )
        AccountService.initialize_account(
            account=account1,
            definition=self.definition
        )

        schema1 = account1.active_schema

        # Create second account of same type
        account2 = Account.objects.create(
            portfolio=self.portfolio,
            name="Account 2",
            account_type=self.account_type,
        )
        AccountService.initialize_account(
            account=account2,
            definition=self.definition
        )

        schema2 = account2.active_schema

        # Should be same schema
        self.assertEqual(schema1.id, schema2.id)

    def test_user_bootstrap_creates_profile_and_portfolio(self):
        """Test that user creation automatically creates Profile and Portfolio."""
        self.assertIsNotNone(self.user.profile)
        self.assertIsNotNone(self.profile.portfolio)
        self.assertTrue(self.portfolio.is_main)
        self.assertEqual(self.portfolio.name, "Main Portfolio")

    def test_account_unique_name_per_type_in_portfolio(self):
        """Test accounts must have unique names per type within a portfolio."""
        # Create first account
        account1 = Account.objects.create(
            portfolio=self.portfolio,
            name="My Account",
            account_type=self.account_type,
        )
        AccountService.initialize_account(
            account=account1,
            definition=self.definition
        )

        # Try to create duplicate name with same type
        with self.assertRaises(IntegrityError):
            Account.objects.create(
                portfolio=self.portfolio,
                name="My Account",
                account_type=self.account_type,
            )

    def test_initialize_account_is_idempotent(self):
        """Test that calling initialize_account multiple times is safe."""
        account = Account.objects.create(
            portfolio=self.portfolio,
            name="Test Account",
            account_type=self.account_type,
        )

        # Initialize once
        AccountService.initialize_account(
            account=account,
            definition=self.definition
        )

        classification_id = account.classification.id
        schema = account.active_schema

        # Initialize again (should not create duplicates)
        AccountService.initialize_account(
            account=account,
            definition=self.definition
        )

        # Should still have same classification and schema
        account.refresh_from_db()
        self.assertEqual(account.classification.id, classification_id)
        self.assertEqual(account.active_schema.id, schema.id)