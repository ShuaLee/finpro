from django.db import models
from django.core.exceptions import ValidationError

from assets.models.core import Asset
from assets.models.commodity.commodity import CommodityAsset


class PreciousMetalAsset(models.Model):
    """
    Represents a physical precious metal holding
    whose price is derived from an underlying commodity.
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="precious_metal",
    )

    # -------------------------------------------------
    # Identity
    # -------------------------------------------------
    class Metal(models.TextChoices):
        GOLD = "gold", "Gold"
        SILVER = "silver", "Silver"
        PLATINUM = "platinum", "Platinum"
        PALLADIUM = "palladium", "Palladium"

    metal = models.CharField(
        max_length=20,
        choices=Metal.choices,
        db_index=True,
    )

    # -------------------------------------------------
    # Pricing reference
    # -------------------------------------------------
    commodity = models.ForeignKey(
        CommodityAsset,
        on_delete=models.PROTECT,
        related_name="precious_metals",
        help_text="Commodity spot price used for valuation (e.g. GCUSD).",
    )

    # -------------------------------------------------
    # Unit semantics
    # -------------------------------------------------
    class Unit(models.TextChoices):
        TROY_OUNCE = "ozt", "Troy Ounce"
        GRAM = "g", "Gram"
        KILOGRAM = "kg", "Kilogram"

    unit = models.CharField(
        max_length=10,
        choices=Unit.choices,
        default=Unit.TROY_OUNCE,
        help_text="Unit that the commodity price refers to.",
    )

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------
    def clean(self):
        super().clean()

        if self.asset.asset_type.slug != "precious_metal":
            raise ValidationError(
                "PreciousMetalAsset must attach to precious_metal assets."
            )

        if self.commodity.asset.asset_type.slug != "commodity":
            raise ValidationError(
                "PreciousMetalAsset must derive from a commodity asset."
            )

    # -------------------------------------------------
    # Pricing
    # -------------------------------------------------
    @property
    def price(self):
        """
        Returns the spot price per declared unit.
        """
        asset_price = getattr(self.commodity.asset, "price", None)
        if not asset_price:
            return None
        return asset_price.price

    @property
    def currency(self):
        """
        Currency is inherited from the commodity.
        """
        return self.commodity.currency

    def __str__(self):
        return f"{self.get_metal_display()} ({self.unit})"
    
    @property
    def reconciliation_key(self) -> str:
        return self.metal.lower()