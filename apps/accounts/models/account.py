from django.core.exceptions import ValidationError
from django.db import models
from accounts.constants import AccountType
from portfolios.models.subportfolio import SubPortfolio


class Account(models.Model):
    """
    Unified account model across all asset classes.

    - Every account belongs to a SubPortfolio.
    - Differentiated by `type`.
    - Extension tables hold special-case fields.
    """

    subportfolio = models.ForeignKey(
        SubPortfolio,
        on_delete=models.CASCADE,
        related_name="accounts"
    )

    name = models.CharField(max_length=100)
    type = models.CharField(
        max_length=30,
        choices=AccountType.choices,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_synced = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            # Prevent duplicate names in the same subportfolio.
            models.UniqueConstraint(
                fields=["subportfolio", "name"],
                name="uniq_account_name_in_subportfolio",
            )
        ]

    def clean(self):
        """
        Ensure account type matches subportfolio type.
        """
        type_to_subportfolio = {
            AccountType.STOCK_SELF_MANAGED: "stock",
            AccountType.STOCK_MANAGED: "stock",
            AccountType.CRYPTO_WALLET: "crypto",
            AccountType.METAL_STORAGE: "metal",
            AccountType.CUSTOM: "custom",
        }

        expected_type = type_to_subportfolio.get(self.type)
        if expected_type and self.subportfolio.type != expected_type:
            raise ValidationError(
                f"Account type '{self.get_type_display()}' "
                f"can only be added to a '{expected_type}' subportfolio."
            )

    def __str__(self):
        return f"{self.get_type_display()} ({self.name})"

    @property
    def profile(self):
        """Convenience to fetch profile via subportfolio → portfolio → profile."""
        return self.subportfolio.portfolio.profile

    @property
    def currency(self):
        """Always use the profile's currency."""
        return self.profile.currency

    @property
    def active_schema(self):
        from schemas.models import Schema  # local import to avoid circular deps
        try:
            return Schema.objects.get(
                subportfolio=self.subportfolio,
                account_type=self.type,
            )
        except Schema.DoesNotExist:
            return None
