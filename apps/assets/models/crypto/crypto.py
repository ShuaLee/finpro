from django.core.exceptions import ValidationError
from django.db import models

from assets.models.core import Asset
from fx.models.fx import FXCurrency

class CryptoAsset(models.Model):
    """
    Represents a cryptocurrency asset priced via an external provider (FMP).

    Design principles:
    - One row per crypto (e.g. BTC, ETH, MIOTA)
    - Pricing is always via a quote currency (usually USD)
    - Safe to delete and rebuild frequently
    - No historical assumptions
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="crypto",
    )

    # -------------------------
    # Identity
    # -------------------------
    base_symbol = models.CharField(
        max_length=20,
        db_index=True,
        help_text="Base crypto symbol (e.g. BTC, ETC, MIOTA).",
    )

    pair_symbol = models.CharField(
        max_length=30,
        unique=True,
        help_text="Provider pricing pair (e.g. BTCUSD).",
    )

    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Human-readable name (e.g. Bitcoin, Ethereum).",
    )

    # -------------------------
    # Pricing
    # -------------------------
    currency = models.ForeignKey(
        FXCurrency,
        on_delete=models.PROTECT,
        related_name="crypto_assets",
        help_text="Currency this crypto is priced in (usually USD).",
    )

    # -------------------------
    # Supply (optional metadata)
    # -------------------------
    circulating_supply = models.DecimalField(
        max_digits=30,
        decimal_places=10,
        null=True,
        blank=True,
    )

    total_supply = models.DecimalField(
        max_digits=30,
        decimal_places=10,
        null=True,
        blank=True,
    )

    # -------------------------
    # Lifecycle
    # -------------------------
    ico_date = models.DateField(
        null=True,
        blank=True,
        help_text="ICO / genesis date if available.",
    )

    last_synced = models.DateTimeField(
        auto_now=True,
        help_text="Last time this crypto was synced from provider.",
    )

    # -------------------------
    # Validation
    # -------------------------
    def clean(self):
        if self.asset.asset_type.slug != "crypto":
            raise ValidationError(
                "CryptoAsset may only attach to crypto assets."
            )
        
    @property
    def display_name(self) -> str:
        if self.name:
            return f"{self.base_symbol} - {self.name}"
        return self.base_symbol
    
    def __str__(self):
        return self.display_name