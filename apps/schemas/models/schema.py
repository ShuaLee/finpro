from django.core.exceptions import ValidationError
from django.db import models


class Schema(models.Model):
    """
    Defines the column layout for a given account type
    within a portfolio.

    One schema per (portfolio, account_type).
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

    def __str__(self):
        return f"{self.portfolio} — {self.account_type.name} Schema"
