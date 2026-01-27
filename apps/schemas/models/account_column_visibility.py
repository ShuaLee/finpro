from django.db import models


class AccountColumnVisibility(models.Model):
    """
    Presentation-only visibility of a SchemaColumn for a specific Account.

    Does NOT affect:
    - computation
    - formulas
    - analytics
    """

    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        related_name="column_visibility",
    )

    column = models.ForeignKey(
        "schemas.SchemaColumn",
        on_delete=models.CASCADE,
        related_name="account_visibility",
    )

    is_visible = models.BooleanField(default=True)

    class Meta:
        unique_together = ("account", "column")

    def __str__(self):
        return f"{self.account_id}:{self.column.identifier}={self.is_visible}"
