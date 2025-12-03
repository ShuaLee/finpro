from django.db import models
from assets.models.assets import Asset
from core.types import DomainType


class CryptoDetail(models.Model):
    """
    Reference data for cryptocurrencies from providers.
    Automatically synchronized from FMP.
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="crypto_detail",
        limit_choices_to={"asset_type__domain": DomainType.CRYPTO},
    )

    # Decimal place precision
    quantity_precision = models.PositiveIntegerField(
        default=18)   # BTC=8, XRP=6, etc

    # project metadata (FMP doesn't supply, but room for expansion)
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)

    # FMP metadata
    exchange = models.CharField(max_length=50, null=True, blank=True)

    is_custom = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def base_symbol(self):
        ident = self.asset.identifiers.filter(
            id_type="BASE_SYMBOL"
        ).first()
        return ident.value if ident else None

    @property
    def pair_symbol(self):
        ident = self.asset.identifiers.filter(
            id_type="PAIR_SYMBOL"
        ).first()
        return ident.value if ident else None

    def __str__(self):
        pid = self.asset.primary_identifier
        return f"{pid.value if pid else self.asset.name}"

    def _sync_precision_change(self, old):
        """
        If quantity_precision changes, update all SCVs for holdings
        referencing this asset.
        """
        from schemas.services.schema_manager import SchemaManager

        old_precision = getattr(
            old, "quantity_precision", None) if old else None
        new_precision = self.quantity_precision

        # No changee -> Nothing to do
        if old_precision == new_precision:
            return

        # Fetch all holdings that own this asset
        holdings = self.asset.holdings.all()

        for holding in holdings:
            schema = holding.active_schema
            if not schema:
                continue

            manager = SchemaManager(schema)

            # Rebuild SCVs using new precision
            manager.sync_for_holding(holding)

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        # Load old instance to compare precision
        if not is_new:
            old = CryptoDetail.objects.get(pk=self.pk)
        else:
            old = None

        super().save(*args, **kwargs)

        # Only after save -> sync precision effects
        self._sync_precision_change(old)
