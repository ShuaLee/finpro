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
        constraints = [
            # Asset-backed holdings: one per account-asset pair
            models.UniqueConstraint(
                fields=["account", "asset"],
                condition=models.Q(source="asset"),
                name="unique_account_asset_holding",
            ),
            # Custom holdings: no constraint here, uniqueness enforced via schema identifier column
        ]
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
        if not self.account or not self.account.active_schema:
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
            self.asset = None

            if not self.custom_reason:
                self.custom_reason = self.CUSTOM_REASON_USER

            # Custom holdings do not participate in asset logic
            return

        # -------------------------------------------------
        # SOURCE_ASSET: strict validation
        # -------------------------------------------------
        if not self.asset:
            raise ValidationError(
                "Asset-backed holdings must reference an asset."
            )

        # -------------------------------------------------
        # Derive original_ticker from asset (single source of truth)
        # -------------------------------------------------
        def derive_original_ticker(asset):
            equity = getattr(asset, "equity", None)
            crypto = getattr(asset, "crypto", None)
            commodity = getattr(asset, "commodity", None)
            precious_metal = getattr(asset, "precious_metal", None)
            custom = getattr(asset, "custom", None)

            if equity and equity.ticker:
                return equity.ticker

            if crypto and crypto.base_symbol:
                return crypto.base_symbol

            if commodity and commodity.symbol:
                return commodity.symbol

            if precious_metal:
                return precious_metal.reconciliation_key

            if custom and custom.name:
                return custom.name

            raise ValidationError(
                "Asset-backed holdings must have a derivable original_ticker."
            )

        # -------------------------------------------------
        # Refresh original_ticker if asset changed OR missing
        # -------------------------------------------------
        new_ticker = derive_original_ticker(self.asset)

        if self.pk:
            old_asset_id = (
                type(self)
                .objects
                .filter(pk=self.pk)
                .values_list("asset_id", flat=True)
                .first()
            )
        else:
            old_asset_id = None

        if not self.original_ticker or old_asset_id != self.asset_id:
            self.original_ticker = new_ticker

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
