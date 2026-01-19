from django.db import models
from django.core.exceptions import ValidationError

from accounts.models.account import Account


class Holding(models.Model):
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="holdings",
    )

    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.CASCADE,
        related_name="holdings",
    )

    quantity = models.DecimalField(
        max_digits=50,
        decimal_places=30,
        default=0,
        help_text="Total quantity of this asset held in the account.",
    )

    average_purchase_price = models.DecimalField(
        max_digits=50,
        decimal_places=30,
        null=True,
        blank=True,
        help_text="Weighted average purchase price per unit.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("account", "asset")
        ordering = ["account", "asset"]

    def __str__(self):
        return f"{self.quantity} {self.asset} in {self.account.name}"

    # ------------------------
    # Validation
    # ------------------------
    def clean(self):
        super().clean()

        # ---- Quantity rules ----
        if self.quantity < 0:
            raise ValidationError(
                {"quantity": "Holding quantity cannot be negative."}
            )

        # ---- Average price rules ----
        if self.average_purchase_price is not None:
            if self.average_purchase_price < 0:
                raise ValidationError(
                    {
                        "average_purchase_price":
                        "Average purchase price cannot be negative."
                    }
                )

            if self.quantity == 0:
                raise ValidationError(
                    {
                        "average_purchase_price":
                        "Average purchase price must be empty when quantity is zero."
                    }
                )

        # ---- AssetType compatibility ----
        account_type = self.account.account_type
        asset_type = self.asset.asset_type

        allowed = account_type.allowed_asset_types.all()
        if allowed.exists() and asset_type not in allowed:
            raise ValidationError(
                f"Accounts of type '{account_type.name}' "
                f"cannot hold assets of type '{asset_type.name}'."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    # ------------------------
    # Derived values
    # ------------------------
    @property
    def current_value(self):
        price = getattr(self.asset, "price", None)
        if price and price.price is not None:
            return self.quantity * price.price
        return None
