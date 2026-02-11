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
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="holdings",
    )

    original_ticker = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        db_index=True,
        help_text="Ticker used when this holding was market-backed.",
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
        constraints = [
            models.UniqueConstraint(
                fields=["account", "asset"],
                name="unique_account_asset_holding",
            )
        ]
        ordering = ["account", "asset"]

    def __str__(self):
        return f"{self.quantity} {self.asset.display_name} in {self.account.name}"

    # ------------------------
    # Validation
    # ------------------------

    def clean(self):
        super().clean()

        # -----------------------------
        # Account invariant
        # -----------------------------
        if not self.account or not self.account.active_schema:
            raise ValidationError(
                "Account schema must exist before holdings can be created."
            )

        # -----------------------------
        # Asset required
        # -----------------------------
        if not self.asset:
            raise ValidationError("Holding must reference an asset.")

        # -----------------------------
        # Quantity rules
        # -----------------------------
        if self.quantity < 0:
            raise ValidationError(
                {"quantity": "Holding quantity cannot be negative."}
            )

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

        # -----------------------------
        # AssetType compatibility
        # -----------------------------
        allowed = self.account.account_type.allowed_asset_types.all()
        if allowed.exists() and self.asset.asset_type not in allowed:
            raise ValidationError(
                f"Accounts of type '{self.account.account_type.name}' "
                f"cannot hold assets of type '{self.asset.asset_type.name}'."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
