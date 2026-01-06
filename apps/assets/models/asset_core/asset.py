import uuid
from django.db import models
# from django.contrib.postgres.fields import ArrayField -> this when postgre
from django.core.exceptions import ValidationError
from fx.models.fx import FXCurrency


class Asset(models.Model):
    """
    Base universal asset/security record (Security Master).
    Stores minimal universal data. Details live in subtype tables.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    asset_type = models.ForeignKey(
        "assets.AssetType",
        on_delete=models.PROTECT,
        related_name="assets",
    )

    is_custom = models.BooleanField(
        default=False,
        help_text="True if this asset was manually created (not from external data)."
    )

    currency = models.ForeignKey(
        FXCurrency,
        on_delete=models.PROTECT,
        related_name="assets",
        # some assets may not have a currency (real estate, custom, etc.)
        null=True,
        blank=True,
        help_text="Default currency in which this asset is quoted or valued."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def name(self):
        if hasattr(self, "equity_profile"):
            return self.equity_profile.name
        return None

    @property
    def ticker(self):
        """
        Returns the equity ticker identifier if present.
        """
        return self.identifiers.filter(
            id_type="TICKER"
        ).first()

    @property
    def latest_price(self):
        """
        Convenience accessor: returns the latest (and only) price record.
        """
        price = getattr(self, "asset_price", None)
        return price.price if price else None

    class Meta:
        indexes = [
            models.Index(fields=["asset_type"]),
        ]

    def clean(self):
        super().clean()

        required_identifiers = self.asset_type.identifier_rules

        if required_identifiers and not self.identifiers.exists():
            raise ValidationError(
                f"Asset type '{self.asset_type.slug}' requires at least one identifier "
                f"(Allowed types: {required_identifiers})."
            )

    def __str__(self):
        ticker = self.identifiers.filter(id_type="TICKER").first()
        return f"{ticker.value if ticker else self.name} ({self.asset_type.name})"
