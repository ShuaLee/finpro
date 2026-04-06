import uuid

from django.core.exceptions import ValidationError
from django.db import models


class Asset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    asset_type = models.ForeignKey(
        "assets.AssetType",
        on_delete=models.PROTECT,
        related_name="assets",
    )
    owner = models.ForeignKey(
        "users.Profile",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="assets",
        help_text="Null means a common/public asset. Set means a private user-owned asset.",
    )

    name = models.CharField(max_length=255)
    symbol = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional ticker, symbol, or shorthand identifier.",
    )
    description = models.TextField(blank=True)

    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Flexible asset-specific metadata.",
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["asset_type", "symbol"],
                condition=(
                    models.Q(owner__isnull=True)
                    & ~models.Q(symbol="")
                ),
                name="uniq_public_asset_symbol_per_type",
            ),
            models.UniqueConstraint(
                fields=["owner", "asset_type", "name"],
                condition=models.Q(owner__isnull=False),
                name="uniq_private_asset_name_per_owner_and_type",
            ),
        ]
        indexes = [
            models.Index(fields=["asset_type", "name"]),
            models.Index(fields=["owner", "asset_type"]),
            models.Index(fields=["symbol"]),
            models.Index(fields=["is_active"]),
        ]

    @property
    def is_public(self) -> bool:
        return self.owner is None

    @property
    def is_market_tracked(self) -> bool:
        market_data = getattr(self, "market_data", None)
        return bool(market_data and market_data.is_tracked)

    @property
    def current_price(self):
        price = getattr(self, "price", None)
        return getattr(price, "price", None)

    def clean(self):
        super().clean()

        self.name = (self.name or "").strip()
        self.symbol = (self.symbol or "").strip().upper()
        self.description = (self.description or "").strip()

        if not self.name:
            raise ValidationError("Asset name is required.")

        if self.pk:
            previous = Asset.objects.select_related(
                "owner", "asset_type").filter(pk=self.pk).first()
            if previous and previous.owner is None:
                if self.owner is not None:
                    raise ValidationError(
                        "Public assets cannot be reassigned to a user.")
                if previous.asset_type.pk != self.asset_type.pk:
                    raise ValidationError(
                        "Public asset type cannot be changed.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.symbol:
            return f"{self.symbol} - {self.name}"
        return self.name
