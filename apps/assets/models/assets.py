import uuid
from django.db import models
from django.core.exceptions import ValidationError
from core.types import DomainType


class Asset(models.Model):
    """
    Base universal asset/security record (Security Master).
    Stores minimal universal data. Details live in subtype tables.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    asset_type = models.CharField(
        max_length=20,
        choices=DomainType.choices,
        db_index=True,
        help_text="General classification (Equity, Bond, Crypto, Metal, RealEstate, Custom, etc.)",
    )

    name = models.CharField(
        max_length=200,
        help_text="Human-readable name (company, property, or custom asset)."
    )

    currency = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Default currency in which this asset is quoted or valued (if applicable)."
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("ACTIVE", "Active"),
            ("INACTIVE", "Inactive"),
            ("DELISTED", "Delisted"),
            ("PENDING", "Pending/IPO"),
        ],
        default="ACTIVE",
        db_index=True,
        help_text="Listing/availability status of the asset."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["asset_type"]),
            models.Index(fields=["status"]),
        ]

    def clean(self):
        super().clean()
        # Example enforcement: Tradables must have identifiers
        if self.asset_type in {
            DomainType.EQUITY,
            DomainType.BOND,
            DomainType.CRYPTO,
            DomainType.METAL,
        } and not self.identifiers.exists():
            raise ValidationError(
                f"{self.asset_type} assets must have at least one identifier (Ticker, ISIN, etc.)."
            )

    def __str__(self):
        # Prefer a primary identifier if available
        primary_id = self.identifiers.filter(is_primary=True).first()
        return f"{primary_id.value if primary_id else self.name} ({self.asset_type})"


class AssetIdentifier(models.Model):
    """
    Cross-reference identifiers for an asset.
    An asset can have multiple identifiers (Ticker, ISIN, CUSIP, InternalCode).
    """
    class IdentifierType(models.TextChoices):
        TICKER = "TICKER", "Ticker"
        ISIN = "ISIN", "ISIN"
        CUSIP = "CUSIP", "CUSIP"
        CIK = "CIK", "CIK"
        FIGI = "FIGI", "FIGI"
        INTERNAL = "INTERNAL", "Internal Code"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="identifiers"
    )
    id_type = models.CharField(
        max_length=20,
        choices=IdentifierType.choices,
        db_index=True,
    )
    value = models.CharField(max_length=50, db_index=True)
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

    def clean(self):
        super().clean()
        # Ensure only one primary identifier per asset
        if self.is_primary:
            qs = AssetIdentifier.objects.filter(
                asset=self.asset, is_primary=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    "An asset can only have one primary identifier.")

    def __str__(self):
        return f"{self.id_type}: {self.value}"
