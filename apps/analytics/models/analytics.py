from django.core.exceptions import ValidationError
from django.db import models


class Analytic(models.Model):
    """
    Represents a single analytic definition for a user's profile.
    Examples:
        - "Country Exposure"
        - "Sector Breakdown"
        - "ESG Theme Exposure"

    Each analytic belongs to a profile and contains one or more analytic
    dimensions that specify how values are grouped.
    """

    profile = models.ForeignKey(
        "users.Profile",
        on_delete=models.CASCADE,
        related_name="analytics"
    )

    name = models.CharField(max_length=100)
    label = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("profile", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.profile.user.email}: {self.name}"


class AnalyticDimension(models.Model):
    """
    A dimension represents a specific grouping inside an analytic.
    Examples:
        Analytic = Country Exposure
            Dimensions = "Country"

        Analytic = Sector Breakdown
            Dimensions = "GICS Sector", "Industry Group"

    Most analytics use exactly one dimension,
    but multi-dimensional analytics are supported.
    """
    analytic = models.ForeignKey(
        Analytic,
        on_delete=models.CASCADE,
        related_name="dimensions"
    )

    name = models.CharField(max_length=100)
    label = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("analytic", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.analytic.name} -> {self.name}"


class AnalyticDimensionValue(models.Model):
    """
    Stores the computed values for a single dimension bucket.
    Example entries for a 'Country Exposure' dimension:
        - dimension_value = "USA", total_value=40000, percentage=0.30
        - dimension_value = "Canada", total_value=15000, percentage=0.12
        - dimension_value = "Unknown", total_value=80000, percentage=0.58

    These values are *ephemeral*—they are overwritten every time analytics
    are recomputed.
    """
    dimension = models.ForeignKey(
        AnalyticDimension,
        on_delete=models.CASCADE,
        related_name="analytic_values"
    )

    dimension_value = models.CharField(max_length=255)

    total_value = models.DecimalField(max_digits=20, decimal_places=2)
    percentage = models.DecimalField(max_digits=10, decimal_places=4)

    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("dimension", "dimension_value")
        ordering = ["dimension_value"]

    def __str__(self):
        return f"{self.dimension.name}: {self.dimension_value}"
