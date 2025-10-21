from django.core.exceptions import ValidationError
from django.db import transaction


class AccountService:
    @staticmethod
    @transaction.atomic
    def initialize_account(account, definition, profile):
        """
        Fully initialize an account after creation:
        - Ensure the proper AccountClassification exists and is linked
        - Validate account consistency
        - Ensure schema exists for the account’s (portfolio, account_type)
        """

        from accounts.models.account_classification import AccountClassification
        from schemas.services.schema_manager import SchemaManager

        # ✅ 1. Get or create classification
        classification, _ = AccountClassification.objects.get_or_create(
            profile=profile,
            definition=definition,
        )

        # ✅ 2. Update classification if needed
        if account.classification_id != classification.id:
            account.classification = classification

        # ✅ 3. Validate full account before saving
        try:
            account.full_clean()
        except ValidationError as e:
            raise ValidationError(
                f"Failed to initialize account '{account.name}' "
                f"with classification '{definition.name}': {e}"
            )

        # ✅ 4. Save safely (only changed fields)
        account.save()

        # ✅ 5. Ensure schema exists for this account’s type
        SchemaManager.ensure_for_account(account)

        return account
