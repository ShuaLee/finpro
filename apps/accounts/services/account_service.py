from django.core.exceptions import ValidationError
from django.db import transaction


class AccountService:
    @staticmethod
    @transaction.atomic
    def assign_classification(account, definition, profile):
        """
        Ensure the account is linked to the correct AccountClassification.
        Creates one if it doesn't exist for this profile/definition.
        """

        from accounts.models.account_classification import AccountClassification

        # Get or create the user's classification instance
        classification, _ = AccountClassification.objects.get_or_create(
            profile=profile,
            definition=definition
        )

        # Only update if it's different
        if account.classification_id != classification.id:
            account.classification = classification

            # Validate before saving (but avoid double full_clean on get_or_create)
            try:
                account.full_clean()
            except ValidationError as e:
                raise ValidationError(
                    f"Failed to assign classification '{definition.name}' "
                    f"to account '{account.name}': {e}"
                )

            # Save only the changed field
            account.save(update_fields=["classification"])

        return account
