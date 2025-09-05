from django.db import models
from accounts.constants import AccountType
from portfolios.models.subportfolio import SubPortfolio
from common.utils.country_currency_catalog import get_common_currency_choices

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

    currency = models.CharField(
        max_length=3,
        choices=get_common_currency_choices(),
        default="USD",
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

    def __str__(self):
        return f"{self.get_type_display()} ({self.name})"
    
    @property
    def profile(self):
        """Convenience to fetch profile via subportfolio → portfolio → profile."""
        return self.subportfolio.portfolio.profile
    
    @property
    def active_schema(self):
        """Look up schema for this account based on type."""
        return self.subportfolio.get_schema_for_account_model(self.type)