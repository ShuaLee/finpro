import uuid
from django.db import models


class Asset(models.Model):
    """
    Central reference asset.

    - One row per real-world asset (e.g. AAPL, BTC, House #123)
    - Not owned by users (except custom assets)
    - Extended by type-specific tables (Equity, Crypto, etc.)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    asset_type = models.ForeignKey(
        "assets.AssetType",
        on_delete=models.PROTECT,
        related_name="assets",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["asset_type"]),
        ]

    def __str__(self):
        return f"{self.asset_type.slug.upper()} - {self.id}"

    @property
    def extension(self):
        return getattr(self, self.asset_type.slug, None)
