from django.db import models
from django.core.exceptions import ValidationError

from accounts.models.account import Account


class Holding(models.Model):

    SOURCE_ASSET = "asset"
    SOURCE_CUSTOM = "custom"

    CUSTOM_REASON_USER = "user"
    CUSTOM_REASON_MARKET = "market"

    source = models.CharField(
        max_length=20,
        choices=[
            (SOURCE_ASSET, "Market Asset"),
            (SOURCE_CUSTOM, "Custom Asset"),
        ],
        default=SOURCE_ASSET,
    )

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

    custom_reason = models.CharField(
        max_length=20,
        choices=[
            (CUSTOM_REASON_USER, "User initiated"),
            (CUSTOM_REASON_MARKET, "Market unavailable"),
        ],
        null=True,
        blank=True,
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

        # -------------------------------------------------
        # Account invariant (always required)
        # -------------------------------------------------
        if not self.account.active_schema:
            raise ValidationError(
                "Account schema must exist before holdings can be created."
            )

        # -------------------------------------------------
        # Quantity rules (always apply)
        # -------------------------------------------------
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

        # -------------------------------------------------
        # SOURCE_CUSTOM: normalize + exit asset logic
        # -------------------------------------------------
        if self.source == self.SOURCE_CUSTOM:
            # Custom holdings never reference assets
            self.asset = None

            # Ensure intent is recorded
            if not self.custom_reason:
                self.custom_reason = self.CUSTOM_REASON_USER

            # Custom holdings do not participate in asset rules
            return

        # -------------------------------------------------
        # SOURCE_ASSET: strict validation
        # -------------------------------------------------
        if not self.asset:
            raise ValidationError(
                "Asset-backed holdings must reference an asset."
            )

        # -------------------------------------------------
        # Populate original_ticker (ALL asset types)
        # -------------------------------------------------
        if not self.original_ticker:
            equity = getattr(self.asset, "equity", None)
            crypto = getattr(self.asset, "crypto", None)
            commodity = getattr(self.asset, "commodity", None)
            custom = getattr(self.asset, "custom", None)

            if equity and equity.ticker:
                self.original_ticker = equity.ticker
            elif crypto and crypto.base_symbol:
                self.original_ticker = crypto.base_symbol
            elif commodity and commodity.symbol:
                self.original_ticker = commodity.symbol
            elif custom and custom.name:
                # Defensive fallback (should rarely happen)
                self.original_ticker = custom.name
            else:
                raise ValidationError(
                    "Asset-backed holdings must have original_ticker set."
                )

        # Asset-backed holdings cannot have custom_reason
        self.custom_reason = None

        # -------------------------------------------------
        # AssetType compatibility (AccountType enforcement)
        # -------------------------------------------------
        account_type = self.account.account_type
        asset_type = self.asset.asset_type

        allowed = account_type.allowed_asset_types.all()
        if allowed.exists() and asset_type not in allowed:
            raise ValidationError(
                f"Accounts of type '{account_type.name}' "
                f"cannot hold assets of type '{asset_type.name}'."
            )

    def save(self, *args, **kwargs):
        if self.source == self.SOURCE_CUSTOM:
            self.asset = None

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
