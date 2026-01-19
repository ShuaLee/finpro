from django.db import transaction


class AccountService:
    @staticmethod
    @transaction.atomic
    def initialize_account(*, account, definition, profile=None):
        """
        Fully initialize an account after creation:
        - Attach AccountClassification
        - Ensure schema exists for (portfolio, account_type)
        """

        from accounts.models.account_classification import AccountClassification
        # from schemas.services.schema_manager import SchemaManager

        # 1️⃣ Get or create classification
        # ✅ Always derive profile from account — never trust caller
        profile = account.portfolio.profile

        classification, _ = AccountClassification.objects.get_or_create(
            profile=profile,
            definition=definition,
        )

        # 2️⃣ Attach classification if not already set
        if account.classification_id != classification.id:
            account.classification = classification
            account.save(update_fields=["classification"])

        # 3️⃣ Ensure schema exists for this account type
        # SchemaManager.ensure_for_account(account)

        return account
