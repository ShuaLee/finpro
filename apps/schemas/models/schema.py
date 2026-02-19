from django.core.exceptions import ValidationError
from django.db import models


class Schema(models.Model):
    """
    Shared schema for a (portfolio, account_type).

    All accounts of the same account_type within a portfolio share this schema.
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
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("portfolio", "account_type")
        ordering = ["account_type__slug"]

    def clean(self):
        super().clean()
        if self.account_type and not self.account_type.is_system:
            if self.account_type.owner_id != self.portfolio.profile_id:
                raise ValidationError(
                    "Custom account type must belong to the same profile as the portfolio."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.portfolio} - {self.account_type.name} Schema"
