from django.core.exceptions import ValidationError


class AccountService:
    @staticmethod
    def assign_classification(account, definition, profile):
        from accounts.models.account_classification import AccountClassification
        classification, _ = AccountClassification.objects.get_or_create(
            profile=profile,
            definition=definition
        )
        account.classification = classification
        account.full_clean()
        account.save()
        return account
