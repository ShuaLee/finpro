from django.core.exceptions import ValidationError
from django.db import models


class Analytic(models.Model):
    """
    Represents a single analytic configured for a portfolio.

    Examples:
        - "Country Exposure"
        - "Sector Breakdown"
        - "Asset Class Allocation"
        - "ESG Theme Exposure"

    Each Analytic defines:
        - A user-visible name/label
        - The schema column identifier to SUM (e.g., current_value_profile_fx)
        - One or more dimensions that determine grouping
    """

    portfolio = models.ForeignKey(
        "portfolios.Portfolio",
        on_delete=models.CASCADE,
        related_name="analytics",
        help_text="The portfolio this analytic belongs to."
    )

    name = models.CharField(
        max_length=100,
        help_text="Internal identifier for this analytic (unique per portfolio)."
    )

    label = models.CharField(
        max_length=150,
        help_text="User-visible label, e.g. 'Country Exposure'."
    )

    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional description of what this analytic measures."
    )

    # What measure to sum? Typically a SchemaColumn.identifier
    value_identifier = models.CharField(
        max_length=100,
        help_text="SchemaColumn identifier used for aggregation (e.g., 'current_value_profile_fx')."
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("portfolio", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.portfolio.profile.user.email}: {self.name}"


class AnalyticDimension(models.Model):
    """
    A grouping key for an Analytic.
    Examples:
        - country
        - sector
        - industry_group
        - theme
        - asset_class

    The dimension name maps to a SchemaColumn.identifier.
    """

    analytic = models.ForeignKey(
        Analytic,
        on_delete=models.CASCADE,
        related_name="dimensions",
    )

    name = models.CharField(
        max_length=100,
        help_text="Internal identifier for this dimension (unique per analytic)."
    )

    label = models.CharField(
        max_length=150,
        help_text="User-facing label (e.g. 'Country', 'Sector')."
    )

    description = models.TextField(blank=True, null=True)

    # What SchemaColumn provides the grouping
    source_identifier = models.CharField(
        max_length=100,
        help_text="SchemaColumn identifier used to group holdings (e.g. 'country', 'sector')."
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("analytic", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.analytic.name} -> {self.name}"


class AnalyticDimensionValue(models.Model):
    """
    Represents one computed bucket of a dimension.
    These records are ephemeral—each recomputation overwrites them.

    For a 'Country Exposure' analytic, dimension values might be:

        - USA → $40,000 → 30%
        - Canada → $15,000 → 12%
        - Unknown → $80,000 → 58%

    The uniqueness is:
        dimension + dimension_value
    """

    dimension = models.ForeignKey(
        AnalyticDimension,
        on_delete=models.CASCADE,
        related_name="values",
    )

    dimension_value = models.CharField(
        max_length=255,
        help_text="Total aggregated numeric value for this bucket."
    )

    total_value = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Total aggregated numeric value for this bucket."
    )

    percentage = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="Percentage of the analytic total that this bucket represents.",
    )

    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("dimension", "dimension_value")
        ordering = ["dimension_value"]

    def __str__(self):
        return f"{self.dimension.name}: {self.dimension_value}"
