from django.db import models
from django.core.exceptions import ValidationError
from accounts.models.account import Account
from assets.models.assets import Asset
from core.types import get_domain_meta


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
        max_digits=50,
        decimal_places=30,
        default=0,
        help_text="Number of units owned (shares, coins, ounces, etc.)",
    )
    purchase_price = models.DecimalField(
        max_digits=50,
        decimal_places=30,
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
        primary_id = getattr(self.asset.primary_identifier, "value", None)
        symbol = primary_id or getattr(self.asset, "name", "Unknown")
        return f"{self.quantity.normalize()} {symbol} in {self.account.name}"

    # ----------------------------
    # Validation
    # ----------------------------
    def clean(self):
        allowed = get_domain_meta(self.account.domain_type)["allowed_assets"]
        if self.asset.asset_type not in allowed:
            raise ValidationError(
                f"{self.account.domain_type} accounts cannot hold {self.asset.asset_type} assets."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        """
        is_new = self._state.adding
        from schemas.services.schema_column_value_manager import SchemaColumnValueManager

        if is_new:
            # 🔑 First time → generate SCVs for all schema columns
            SchemaColumnValueManager.ensure_for_holding(self)
        else:
            # 🔄 On update → refresh values for all SCVs
            SchemaColumnValueManager.refresh_for_holding(self)
        """

    # -----------------------
    # Convenience properties
    # -----------------------
    @property
    def profile_currency(self):
        return self.account.portfolio.profile.currency

    @property
    def active_schema(self):
        return self.account.active_schema

    @property
    def current_value(self):
        """quantity × asset.last_price (if available)."""
        price = getattr(self.asset, "last_price", None)
        return self.quantity * price if price is not None else None
