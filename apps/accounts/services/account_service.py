from django.db import transaction


class AccountService:
    @staticmethod
    @transaction.atomic
    def initialize_account(*, account, definition, profile=None):
        """
        Fully initialize an account after creation:

        - Attach AccountClassification
        - Ensure schema exists for (portfolio, account_type)
        - SCVs created automatically via SchemaManager
        - Idempotent: safe to re-run
        """

        from accounts.models.account_classification import AccountClassification
        from schemas.services.schema_manager import SchemaManager

        # 1️⃣ Always derive profile from account
        profile = account.portfolio.profile

        classification, _ = AccountClassification.objects.get_or_create(
            profile=profile,
            definition=definition,
        )

        # 2️⃣ Attach classification if not already present
        if account.classification_id != classification.id:
            account.classification = classification
            account.save(update_fields=["classification"])

        # 3️⃣ Ensure schema + SCVs are initialized
        SchemaManager.ensure_for_account(account)

        return account
