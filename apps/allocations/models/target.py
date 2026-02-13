from django.core.exceptions import ValidationError
from django.db import models

from .plan import AllocationScenario


class AllocationDimension(models.Model):
    """
    What a scenario is targeting (country, asset class, sector, etc.).

    This uses identifiers instead of hard FK to analytics dimensions so the
    target layer stays stable even if analytics internals evolve.
    """

    class DenominatorMode(models.TextChoices):
        BASE_SCOPE_TOTAL = "base_scope_total", "Percent of Base Scope"
        ABSOLUTE_ONLY = "absolute_only", "Absolute Amount"

    scenario = models.ForeignKey(
        AllocationScenario,
        on_delete=models.CASCADE,
        related_name="dimensions",
    )

    name = models.SlugField(max_length=100)
    label = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)

    source_identifier = models.SlugField(
        max_length=100,
        help_text="Grouping identifier (typically SCV/analytic dimension identifier).",
    )

    denominator_mode = models.CharField(
        max_length=30,
        choices=DenominatorMode.choices,
        default=DenominatorMode.BASE_SCOPE_TOTAL,
    )

    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["scenario", "name"],
                name="uniq_allocation_dimension_name_per_scenario",
            )
        ]
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.scenario.name}:{self.name}"


class AllocationTarget(models.Model):
    """
    Target bucket inside a dimension (e.g., country=AR => 5%).
    """

    dimension = models.ForeignKey(
        AllocationDimension,
        on_delete=models.CASCADE,
        related_name="targets",
    )

    key = models.SlugField(max_length=100)
    label = models.CharField(max_length=150)

    target_percent = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    target_value = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    min_percent = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    max_percent = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    is_locked = models.BooleanField(default=False)
    priority = models.PositiveIntegerField(default=0)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["dimension", "key"],
                name="uniq_allocation_target_key_per_dimension",
            )
        ]
        ordering = ["display_order", "key"]

    def clean(self):
        super().clean()

        if self.target_percent is None and self.target_value is None:
            raise ValidationError("At least one of target_percent or target_value is required.")

        if self.target_percent is not None:
            if self.target_percent < 0 or self.target_percent > 1:
                raise ValidationError("target_percent must be between 0 and 1.")

        if self.min_percent is not None and (self.min_percent < 0 or self.min_percent > 1):
            raise ValidationError("min_percent must be between 0 and 1.")

        if self.max_percent is not None and (self.max_percent < 0 or self.max_percent > 1):
            raise ValidationError("max_percent must be between 0 and 1.")

        if self.min_percent is not None and self.max_percent is not None:
            if self.min_percent > self.max_percent:
                raise ValidationError("min_percent cannot be greater than max_percent.")

    def __str__(self):
        return f"{self.dimension.name}:{self.key}"
