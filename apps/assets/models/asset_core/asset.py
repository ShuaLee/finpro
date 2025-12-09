import uuid
from django.db import models
# from django.contrib.postgres.fields import ArrayField -> this when postgre
from django.core.exceptions import ValidationError
from fx.models.fx import FXCurrency
from users.models import Profile


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

    name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Human-readable name (filled by enrichment for tradables, user-supplied for custom/real estate)."
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
    def primary_identifier(self):
        return self.identifiers.filter(is_primary=True).first()

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
        # Prefer a primary identifier if available
        primary_id = self.identifiers.filter(is_primary=True).first()
        return f"{primary_id.value if primary_id else self.name} ({self.asset_type.name})"


class AssetIdentifier(models.Model):
    """
    Cross-reference identifiers for an asset.
    An asset can have multiple identifiers (Ticker, ISIN, CUSIP, etc.).
    Domain-specific validation ensures only valid identifiers per asset type.
    """
    class IdentifierType(models.TextChoices):
        # --- Equities ---
        TICKER = "TICKER", "Ticker"
        ISIN = "ISIN", "ISIN"
        CUSIP = "CUSIP", "CUSIP"
        CIK = "CIK", "CIK"

        # --- Crypto ---
        BASE_SYMBOL = "BASE_SYMBOL", "Base Symbol"
        PAIR_SYMBOL = "PAIR_SYMBOL", "Pair Symbol"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="identifiers",
    )
    id_type = models.CharField(
        max_length=30,
        choices=IdentifierType.choices,
        db_index=True,
    )
    value = models.CharField(max_length=100, db_index=True)
    is_primary = models.BooleanField(
        default=False,
        help_text="Marks the main identifier to display/use in trading.",
    )

    class Meta:
        unique_together = ("id_type", "value")
        indexes = [
            models.Index(fields=["id_type", "value"]),
            models.Index(fields=["asset", "is_primary"]),
        ]

    # ---------------------------------------------------------------
    # Validation rules: enforce one primary + domain-specific id types
    # ---------------------------------------------------------------
    def clean(self):
        super().clean()

        # Enforce exactly one primary identifier per asset
        if self.is_primary:
            existing_primary = self.asset.identifiers.filter(is_primary=True)
            if self.pk:
                existing_primary = existing_primary.exclude(pk=self.pk)
            if existing_primary.exists():
                raise ValidationError(
                    "An asset can only have one primary identifier."
                )

        # Use AssetType.identifier_rules instead of domain registry
        allowed = self.asset.asset_type.identifier_rules or []

        if allowed and self.id_type not in allowed:
            raise ValidationError(
                f"Identifier type '{self.id_type}' is not valid for asset type "
                f"'{self.asset.asset_type.slug}'. Allowed: {allowed}"
            )

    def save(self, *args, **kwargs):
        # Validate before saving
        self.clean()

        # Auto-mark first identifier as primary if none exist
        if not self.asset.identifiers.exists():
            self.is_primary = True

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id_type}: {self.value}"
