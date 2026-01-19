from django.db import models
from django.core.exceptions import ValidationError

from accounts.models.account_classification import AccountClassification
from accounts.models.account_type import AccountType


class Account(models.Model):
    portfolio = models.ForeignKey(
        "portfolios.Portfolio",
        on_delete=models.CASCADE,
        related_name="accounts",
    )

    name = models.CharField(max_length=100)

    account_type = models.ForeignKey(
        AccountType,
        on_delete=models.PROTECT,
        related_name="accounts",
        help_text="The type of account (brokerage, crypto wallet, real estate container, etc.)",
    )

    broker = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Optional broker name.",
    )

    classification = models.ForeignKey(
        AccountClassification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounts",
        help_text="User-specific classification (e.g., TFSA, RRSP, 401k).",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_synced = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["portfolio", "account_type", "name"],
                name="uniq_account_name_in_portfolio_per_type",
            )
        ]
        ordering = ["portfolio", "name"]

    def __str__(self):
        return f"{self.name} [{self.account_type.slug}]"

    # ---------- Convenience ----------

    @property
    def allowed_asset_types(self):
        return self.account_type.allowed_asset_types.all()

    @property
    def profile(self):
        return self.portfolio.profile

    @property
    def currency(self):
        return self.profile.currency

    # ---------- Validation ----------
    def clean(self):
        super().clean()

        # Classification must match profile
        if self.classification and self.classification.profile != self.profile:
            raise ValidationError(
                f"Classification '{self.classification}' does not belong to this profile."
            )

        # No broker rules — always optional

    # ---------- Save ----------
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    # ---------- Schema ----------

    @property
    def active_schema(self):
        from schemas.models.schema import Schema

        return Schema.objects.filter(
            portfolio=self.portfolio,
            account_type=self.account_type,
        ).first()
