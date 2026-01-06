import uuid
from django.db import models
# from django.contrib.postgres.fields import ArrayField -> this when postgre
from django.core.exceptions import ValidationError

from fx.models.fx import FXCurrency
from users.models.profile import Profile

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

    # -------------------------
    # CUSTOM / OWNERSHIP
    # -------------------------
    is_custom = models.BooleanField(
        default=False,
        help_text="True if this asset was manually created (not from external data)."
    )

    created_by = models.ForeignKey(
        Profile,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="custom_assets",
        help_text="Owner of this asset if is_custom=True. NULL for system assets."
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
    def latest_price(self):
        """
        Convenience accessor: returns the latest (and only) price record.
        """
        price = getattr(self, "asset_price", None)
        return price.price if price else None


    def clean(self):
        super().clean()

        # --- Custom asset rules ---
        if self.is_custom and not self.created_by:
            raise ValidationError(
                "Custom assets (is_custom=True) must have a creator."
            )

        if not self.is_custom and self.created_by:
            raise ValidationError(
                "System assets cannot have a creator."
            )

        # --- Identifier rules ---
        required_identifiers = self.asset_type.identifier_rules or []

        if required_identifiers and not self.identifiers.exists():
            raise ValidationError(
                f"Asset type '{self.asset_type.slug}' requires identifiers: "
                f"{required_identifiers}"
            )
        
    class Meta:
        indexes = [
            models.Index(fields=["asset_type"]),
            models.Index(fields=["is_custom"]),
            models.Index(fields=["created_by"]),
        ]
            

    @property
    def display_name(self):
        """
        Human-friendly display name.
        Delegates to asset-type-specific profiles when available.
        """
        # Equity-specific display logic
        if hasattr(self, "equity_profile"):
            return self.equity_profile.display_name

        # Fallbacks for other asset types (for now)
        ident = self.identifiers.first()
        if ident:
            return ident.value

        return str(self.id)

    def __str__(self):
        return f"{self.display_name} ({self.asset_type.name})"