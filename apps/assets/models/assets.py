import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from core.types import DomainType, get_identifier_rules_for_domain
from fx.models.fx import FXCurrency
from users.models import Profile


class AssetType(models.Model):

    slug = models.SlugField(unique=True)

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    # Internal domain mapping
    domain = models.CharField(
        max_length=20,
        choices=DomainType.choices,
    )

    # Identifier rules for this asset type
    identifier_rules = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text="Allowed identifier types (e.g., TICKER, ISIN, BASE_SYMBOL)",
    )

    # Whether user can delete it or not
    is_system = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        Profile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        if self.is_system:
            raise ValidationError("System AssetTypes cannot be deleted.")
        super().delete(*args, **kwargs)


class Asset(models.Model):
    """
    Base universal asset/security record (Security Master).
    Stores minimal universal data. Details live in subtype tables.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    asset_type = models.ForeignKey(
        AssetType,
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
        # Example enforcement: Tradables must have identifiers
        if self.asset_type.domain in {
            DomainType.EQUITY,
            DomainType.BOND,
            DomainType.CRYPTO,
            DomainType.METAL,
        } and not self.identifiers.exists():
            raise ValidationError(
                f"{self.asset_type.domain} assets must have at least one identifier (Ticker, ISIN, etc.)."
            )

    def __str__(self):
        # Prefer a primary identifier if available
        primary_id = self.identifiers.filter(is_primary=True).first()
        return f"{primary_id.value if primary_id else self.name} ({self.asset_type.name})"

    @property
    def domain(self):
        return self.asset_type.domain


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

        # --- Ensure only one primary identifier per asset ---
        if self.is_primary:
            existing_primary = self.asset.identifiers.filter(is_primary=True)
            if self.pk:
                existing_primary = existing_primary.exclude(pk=self.pk)
            if existing_primary.exists():
                raise ValidationError(
                    "An asset can only have one primary identifier.")

        # --- Domain-based identifier validation ---
        allowed = get_identifier_rules_for_domain(self.asset.domain)

        if self.id_type not in allowed:
            raise ValidationError(
                f"Identifier type '{self.id_type}' is not valid for asset type '{self.asset.domain}'."
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
