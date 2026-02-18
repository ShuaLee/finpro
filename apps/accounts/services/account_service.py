import logging

from django.db import transaction

from accounts.exceptions import AccountInitializationError
from accounts.models.account_classification import AccountClassification

logger = logging.getLogger(__name__)


class AccountService:
    @staticmethod
    @transaction.atomic
    def initialize_account(*, account, definition, profile=None):
        """
        Initialize account foundations.

        Always:
        - attach/create AccountClassification

        Best-effort (if schemas app is enabled):
        - ensure schema for (portfolio, account_type)
        - initialize column visibility for account
        """
        logger.info(
            "Initializing account %s (%s) with classification %s",
            account.id,
            account.name,
            definition.name,
        )

        try:
            profile = profile or account.portfolio.profile

            classification, _ = AccountClassification.objects.get_or_create(
                profile=profile,
                definition=definition,
            )

            if account.classification_id != classification.id:
                account.classification = classification
                account.save(update_fields=["classification"])

            # Optional schema integration.
            try:
                from schemas.services.bootstrap import SchemaBootstrapService
                from schemas.services.mutations import SchemaMutationService
            except Exception:
                logger.info(
                    "Schemas app unavailable; skipping schema initialization for account %s",
                    account.id,
                )
                return account

            schema = SchemaBootstrapService.ensure_for_account(account)
            SchemaMutationService.initialize_visibility_for_account(account=account)
            logger.info(
                "Schema %s ensured for account %s",
                getattr(schema, "id", None),
                account.id,
            )
            return account
        except Exception as exc:
            logger.error(
                "Failed to initialize account %s: %s",
                account.id,
                exc,
                exc_info=True,
            )
            raise AccountInitializationError(
                f"Failed to initialize account {account.id}: {exc}"
            ) from exc
