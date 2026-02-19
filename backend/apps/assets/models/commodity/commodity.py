from django.core.exceptions import ValidationError
from django.db import models

from assets.models.core import Asset
from fx.models.fx import FXCurrency


class CommodityAsset(models.Model):
    """
    Represents a tradable commodity priced via FMP.

    Design principles:
    - One row per commodity symbol (e.g. GCUSD, CLUSD)
    - Safe to delete & rebuild frequently
    - No historical assumptions
    - No yield / income model
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="commodity",
        primary_key=True,
    )

    snapshot_id = models.UUIDField(db_index=True)

    # -------------------------
    # Identity
    # -------------------------
    symbol = models.CharField(
        max_length=30,
        db_index=True,
        help_text="Provider commodity symbol (e.g. GCUSD).",
    )

    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Human-readable name (e.g. Gold Futures).",
    )

    trade_month = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Futures delivery month if applicable (e.g. Dec).",
    )

    exchange = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Exchange name if provided by FMP.",
    )

    # -------------------------
    # Pricing
    # -------------------------
    currency = models.ForeignKey(
        FXCurrency,
        on_delete=models.PROTECT,
        related_name="commodity_assets",
        help_text="Currency this commodity is priced in (USD).",
    )

    # -------------------------
    # Lifecycle
    # -------------------------
    last_synced = models.DateTimeField(
        auto_now=True,
        help_text="Last time this commodity was synced from provider.",
    )

    # -------------------------
    # Validation
    # -------------------------
    def clean(self):
        super().clean()

        # Allow partial construction (e.g. during factory/admin usage)
        if not self.asset:
            return

        if self.asset.asset_type.slug != "commodity":
            raise ValidationError(
                "CommodityAsset may only attach to commodity assets."
            )

    def __str__(self) -> str:
        return self.name or self.symbol
