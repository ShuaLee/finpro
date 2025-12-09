from django.db import models
from django.core.exceptions import ValidationError

from apps.assets.models.asset_core.asset import Asset
from apps.assets.models.asset_core.asset import AssetType


class CryptoDetail(models.Model):
    """
    Reference data for cryptocurrencies.
    Automatically synchronized from FMP, but also supports custom entries.
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="crypto_detail",
    )

    # Decimal place precision (BTC=8, ETH=18, XRP=6)
    quantity_precision = models.PositiveIntegerField(default=18)

    # Project metadata
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)

    # FMP metadata
    exchange = models.CharField(max_length=50, null=True, blank=True)

    is_custom = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    # --------------------------------------
    # Validation: must be crypto asset
    # --------------------------------------
    def clean(self):
        super().clean()

        if self.asset.asset_type.slug != "crypto":
            raise ValidationError(
                f"CryptoDetail can only attach to assets with type slug='crypto', "
                f"but this asset has slug='{self.asset.asset_type.slug}'."
            )

    # --------------------------------------
    # Identifier helpers
    # --------------------------------------
    @property
    def base_symbol(self):
        ident = self.asset.identifiers.filter(id_type="BASE_SYMBOL").first()
        return ident.value if ident else None

    @property
    def pair_symbol(self):
        ident = self.asset.identifiers.filter(id_type="PAIR_SYMBOL").first()
        return ident.value if ident else None

    # --------------------------------------
    # Display
    # --------------------------------------
    def __str__(self):
        pid = self.asset.primary_identifier
        return pid.value if pid else self.asset.name

    # --------------------------------------
    # Precision Change Propagation
    # --------------------------------------
    def _sync_precision_change(self, old):
        """
        If quantity_precision changes, update all SCVs for holdings
        that reference this asset.
        """
        from schemas.services.schema_manager import SchemaManager

        old_precision = getattr(
            old, "quantity_precision", None) if old else None
        new_precision = self.quantity_precision

        if old_precision == new_precision:
            return  # no change

        holdings = self.asset.holdings.all()

        for holding in holdings:
            schema = holding.active_schema
            if not schema:
                continue

            manager = SchemaManager(schema)
            manager.sync_for_holding(holding)

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        old = None
        if not is_new:
            try:
                old = CryptoDetail.objects.get(pk=self.pk)
            except CryptoDetail.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # Only after save
        self._sync_precision_change(old)
