from django.db import models
from django.core.exceptions import ValidationError
from accounts.models.account import Account
from assets.models.asset import Asset


class Holding(models.Model):
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="holdings",
    )
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="holdings",
    )

    # Core ownership fields
    quantity = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        default=0,
        help_text="Number of units owned (shares, coins, ounces, etc.)",
    )
    purchase_price = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        null=True,
        blank=True,
        help_text="Purchase price per unit in account currency",
    )
    purchase_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("account", "asset")
        ordering = ["account", "asset"]

    def __str__(self):
        return f"{self.quantity} {self.asset.symbol} in {self.account.name}"

    # ----------------------------
    # Validation
    # ----------------------------
    def clean(self):
        """
        Ensure the asset type matches the account's domain type.
        """
        if self.asset.asset_type != self.account.domain_type:
            raise ValidationError(
                f"Asset domain '{self.asset.asset_type}' does not match "
                f"account domain '{self.account.domain_type}'."
            )
        super().clean()

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)

        from schemas.services.schema_column_value_manager import SchemaColumnValueManager

        if is_new:
            # 🔑 First time → generate SCVs for all schema columns
            SchemaColumnValueManager.ensure_for_holding(self)
        else:
            # 🔄 On update → refresh values for all SCVs
            SchemaColumnValueManager.refresh_for_holding(self)

    # -----------------------
    # Convenience properties
    # -----------------------
    @property
    def profile_currency(self):
        return self.account.subportfolio.portfolio.profile.currency

    @property
    def active_schema(self):
        return self.account.active_schema

    @property
    def current_value(self):
        """quantity × asset.last_price (if available)."""
        price = getattr(self.asset, "last_price", None)
        return self.quantity * price if price is not None else None
