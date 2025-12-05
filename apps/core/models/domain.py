
from django.db import models
from django.contrib.postgres.fields import ArrayField


class Domain(models.Model):
    """
    Represents a high-level asset/account domain such as:
        - equity
        - crypto
        - real_estate
        - metal
        - bond
        - custom

    Domains control:
        - Which account types belong to them
        - Which asset types are allowed
        - Identifier validation rules
        - Schema generation behavior
        - UI grouping and categorization
    """

    # Stable key used internally (replaces DomainType enum)
    slug = models.SlugField(unique=True, max_length=50)

    # Human-readable label ("Equities", "Crypto", "Real Estate")
    name = models.CharField(max_length=100)

    # Optional description for admin/UI
    description = models.TextField(blank=True, null=True)

    # Whether this domain is system-generated and protected
    is_system = models.BooleanField(
        default=True,
        help_text="If True, this domain cannot be deleted or renamed by end users."
    )

    # The asset types this domain allows (FKs to your AssetType model)
    allowed_asset_types = models.ManyToManyField(
        "assets.AssetType",
        blank=True,
        related_name="domains",
        help_text="List of asset types allowed under this domain."
    )

    # Identifier rules such as TICKER, ISIN, BASE_SYMBOL, etc.
    identifier_rules = ArrayField(
        base_field=models.CharField(max_length=50),
        blank=True,
        default=list,
        help_text="Set of allowed identifier rule names for this domain."
    )

    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "slug"]

    def __str__(self):
        return self.name
