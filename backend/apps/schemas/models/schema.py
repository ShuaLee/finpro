from django.core.exceptions import ValidationError
from django.db import models


class Schema(models.Model):
    """
    Schema scoped either to:
    - a default (portfolio, asset_type) pair, or
    - a legacy/account-specific compatibility path via account_type.
    """

    portfolio = models.ForeignKey(
        "portfolios.Portfolio",
        on_delete=models.CASCADE,
        related_name="schemas",
    )

    account_type = models.ForeignKey(
        "accounts.AccountType",
        on_delete=models.CASCADE,
        related_name="schemas",
        null=True,
        blank=True,
    )

    asset_type = models.ForeignKey(
        "assets.AssetType",
        on_delete=models.CASCADE,
        related_name="schemas",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["portfolio", "asset_type"],
                condition=models.Q(asset_type__isnull=False),
                name="uniq_schema_per_portfolio_asset_type",
            ),
            models.UniqueConstraint(
                fields=["portfolio", "account_type"],
                condition=models.Q(account_type__isnull=False),
                name="uniq_schema_per_portfolio_account_type_legacy",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(asset_type__isnull=False)
                    | models.Q(account_type__isnull=False)
                ),
                name="schema_requires_asset_type_or_account_type",
            ),
        ]
        ordering = ["asset_type__slug", "account_type__slug"]

    def clean(self):
        super().clean()
        if self.account_type and not self.account_type.is_system:
            if self.account_type.owner_id != self.portfolio.profile_id:
                raise ValidationError(
                    "Custom account type must belong to the same profile as the portfolio."
                )
        if self.asset_type and self.asset_type.created_by_id and self.asset_type.created_by_id != self.portfolio.profile_id:
            raise ValidationError(
                "Custom asset type must belong to the same profile as the portfolio."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.asset_type:
            return f"{self.portfolio} - {self.asset_type.name} Schema"
        return f"{self.portfolio} - {self.account_type.name} Schema"
