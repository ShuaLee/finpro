from django.db import models
from django.core.exceptions import ValidationError

from accounts.models.account import Account


class Holding(models.Model):
    class TrackingMode(models.TextChoices):
        ACCOUNT_DEFAULT = "account_default", "Account Default"
        TRACKED = "tracked", "Tracked"
        MANUAL = "manual", "Manual"

    class PriceSourceMode(models.TextChoices):
        ACCOUNT_DEFAULT = "account_default", "Account Default"
        MARKET = "market", "Market"
        MANUAL = "manual", "Manual"
        UNAVAILABLE = "unavailable", "Unavailable"

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
    tracking_mode = models.CharField(
        max_length=20,
        choices=TrackingMode.choices,
        default=TrackingMode.ACCOUNT_DEFAULT,
        help_text="Whether this holding follows the account default, is tracked automatically, or is managed manually.",
    )
    price_source_mode = models.CharField(
        max_length=20,
        choices=PriceSourceMode.choices,
        default=PriceSourceMode.ACCOUNT_DEFAULT,
        help_text="How this holding should be valued when price data is resolved.",
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
        if not self.asset:
            return f"{self.quantity} [MISSING ASSET] in {self.account.name}"
        return f"{self.quantity} {self.asset.display_name} in {self.account.name}"

    @property
    def active_schema(self):
        asset_type = self.asset.asset_type if self.asset_id and self.asset else None
        return self.account.resolve_schema_for_asset_type(asset_type)

    @property
    def effective_tracking_mode(self):
        if self.tracking_mode != self.TrackingMode.ACCOUNT_DEFAULT:
            return self.tracking_mode
        if self.account.position_mode == self.account.PositionMode.MANUAL:
            return self.TrackingMode.MANUAL
        return self.TrackingMode.TRACKED

    @property
    def effective_price_source_mode(self):
        if self.price_source_mode != self.PriceSourceMode.ACCOUNT_DEFAULT:
            return self.price_source_mode
        custom_extension = getattr(self.asset, "custom", None)
        if custom_extension is not None:
            return self.PriceSourceMode.MANUAL
        return self.PriceSourceMode.MARKET

    # ------------------------
    # Validation
    # ------------------------

    def clean(self):
        super().clean()

        if not self.account:
            raise ValidationError("Holding must belong to an account.")

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
        if self.account.enforce_restrictions and not self.account.is_asset_type_allowed(self.asset.asset_type):
            raise ValidationError(
                f"Asset type '{self.asset.asset_type.name}' is not allowed in account '{self.account.name}'."
            )

        # -----------------------------
        # Private asset ownership
        # -----------------------------
        private_owner_id = None
        custom_extension = getattr(self.asset, "custom", None)
        if custom_extension is not None:
            private_owner_id = custom_extension.owner_id
        else:
            extension = self.asset.extension
            if extension is not None and hasattr(extension, "owner_id"):
                private_owner_id = extension.owner_id

        if private_owner_id is not None and private_owner_id != self.account.profile.id:
            raise ValidationError(
                "You cannot attach another user's private asset to this holding."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
