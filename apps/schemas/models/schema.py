from django.db import models


class Schema(models.Model):
    """
    Shared schema for a (portfolio, account_type).

    All accounts of the same account_type within a portfolio
    share this schema.

    Lifecycle:
    - Created when first account of this type is created
    - Deleted when last account of this type is deleted
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
