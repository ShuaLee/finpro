from django.db import models
from django.core.exceptions import ValidationError


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

    def clean(self):
        super().clean()
        if self.account and self.column:
            schema = self.account.resolve_schema_for_asset_type(
                self.column.schema.asset_type
            ) if self.column.schema.asset_type_id else getattr(self.account, "active_schema", None)
            if not schema or self.column.schema_id != schema.id:
                raise ValidationError(
                    "Visibility column must belong to the schema resolved for this account."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.account_id}:{self.column.identifier}={self.is_visible}"
