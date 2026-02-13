import logging

from django.db import transaction

from accounts.exceptions import AccountInitializationError
from accounts.models.account_classification import AccountClassification
from schemas.services.mutations import SchemaMutationService
from schemas.services.bootstrap import SchemaBootstrapService

logger = logging.getLogger(__name__)


class AccountService:
    @staticmethod
    @transaction.atomic
    def initialize_account(*, account, definition, profile=None):
        """
        Fully initialize an account after creation.

        ⚠️  CRITICAL: This method MUST be called after creating any Account instance
        via Django Admin or API endpoints.

        Flow:
            1. Creates/links AccountClassification (profile + definition)
            2. Ensures Schema exists for (portfolio, account_type)
            3. Auto-creates SchemaColumnValues for all holdings in account

        Usage (Admin Pattern):
            # Step 1: Create the account
            account = Account.objects.create(
                portfolio=portfolio,
                name="My Brokerage",
                account_type=brokerage_type,
            )

            # Step 2: Initialize (REQUIRED)
            AccountService.initialize_account(
                account=account,
                definition=tfsa_definition,
            )

        Args:
            account: Account instance to initialize
            definition: ClassificationDefinition (e.g., TFSA, RRSP, 401k)
            profile: Optional, derived from account.portfolio.profile if None

        Returns:
            Account: The initialized account instance

        Raises:
            AccountInitializationError: If SchemaTemplate doesn't exist for account.account_type

        Note:
            - Idempotent: safe to call multiple times
            - Atomic: wrapped in @transaction.atomic
            - Used by: AccountAdmin.save_model()
            - Schema creation happens automatically via SchemaGenerator
        """

        logger.info(
            f"Initializing account {account.id} ({account.name}) "
            f"with classification {definition.name}"
        )

        try:
            # 1️⃣ Always derive profile from account
            profile = account.portfolio.profile

            classification, created = AccountClassification.objects.get_or_create(
                profile=profile,
                definition=definition,
            )

            if created:
                logger.info(
                    f"Created new classification {classification.id} for profile {profile.id}")

            # 2️⃣ Attach classification if not already present
            if account.classification_id != classification.id:
                account.classification = classification
                account.save(update_fields=["classification"])
                logger.info(
                    f"Attached classification {classification.id} to account {account.id}")

            # 3️⃣ Ensure schema + SCVs are initialized
            schema = SchemaBootstrapService.ensure_for_account(account)

            SchemaMutationService.initialize_visibility_for_account(
                account=account)

            logger.info(
                f"Schema {schema.id} ensured for account {account.id} "
                f"(portfolio: {account.portfolio.id}, type: {account.account_type.slug})"
            )

            logger.info(f"Account {account.id} initialized successfully")
            return account

        except Exception as e:
            logger.error(
                f"Failed to initialize account {account.id}: {str(e)}",
                exc_info=True
            )
            raise AccountInitializationError(
                f"Failed to initialize account {account.id}: {str(e)}"
            ) from e
