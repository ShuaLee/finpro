from django.db import models
from accounts.models.account import Account


class AssetType(models.TextChoices):
    STOCK = "stock", "Stock"
    CRYPTO = "crypto", "Crypto"
    METAL = "metal", "Metal"
    CUSTOM = "custom", "Custom"


class Asset(models.Model):
    asset_type = models.CharField(max_length=20, choices=AssetType.choices)
    symbol = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("asset_type", "symbol")

    def __str__(self):
        return f"{self.symbol} ({self.asset_type})"


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

    # Pro-level: always max safe precision, rules enforced by schema configs
    quantity = models.DecimalField(max_digits=30, decimal_places=12, default=0)
    purchase_price = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        null=True,
        blank=True,
        help_text="Price per unit in account currency at purchase time",
    )
    purchase_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} {self.asset.symbol} in {self.account.name}"

    @property
    def profile_currency(self):
        return self.account.subportfolio.portfolio.profile.currency

    @property
    def active_schema(self):
        return self.account.active_schema
