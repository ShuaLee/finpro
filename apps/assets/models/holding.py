from django.db import models
from django.core.exceptions import ValidationError
from accounts.models.account import Account
from assets.models.assets import Asset


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

    quantity = models.DecimalField(
        max_digits=50,
        decimal_places=30,
        default=0,
    )
    purchase_price = models.DecimalField(
        max_digits=50,
        decimal_places=30,
        null=True,
        blank=True,
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

    # ------------------------
    # Validation
    # ------------------------
    def clean(self):
        account_type = self.account.account_type
        asset_type = self.asset.asset_type

        allowed = account_type.allowed_asset_types.all()

        if asset_type not in allowed:
            raise ValidationError(
                f"Accounts of type '{account_type.name}' "
                f"cannot hold assets of type '{asset_type.name}'."
            )

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        self.full_clean()
        super().save(*args, **kwargs)

        from schemas.services.schema_column_value_manager import SchemaColumnValueManager

        if is_new:
            SchemaColumnValueManager.ensure_for_holding(self)
        else:
            SchemaColumnValueManager.refresh_for_holding(self)

    # ------------------------
    # Convenience
    # ------------------------
    @property
    def profile_currency(self):
        return self.account.portfolio.profile.currency

    @property
    def active_schema(self):
        return self.account.active_schema

    @property
    def current_value(self):
        """quantity × asset.market_data.last_price (if present)."""
        mdc = getattr(self.asset, "market_data", None)
        if mdc and mdc.last_price is not None:
            return self.quantity * mdc.last_price
        return None
