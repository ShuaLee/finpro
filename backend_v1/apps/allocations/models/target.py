from django.core.exceptions import ValidationError
from django.db import models

from .plan import AllocationScenario


class AllocationDimension(models.Model):
    """
    Targeting dimension linked to analytics output.

    source_identifier expects the analytics dimension name (slug).
    source_analytic_name can be provided to disambiguate when multiple analytics
    contain the same dimension name.
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
        help_text="Analytics dimension name (slug).",
    )
    source_analytic_name = models.SlugField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Optional analytics name to disambiguate dimension source.",
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
        indexes = [models.Index(fields=["scenario", "is_active", "display_order"]) ]

    def clean(self):
        super().clean()

        if self.pk:
            original = AllocationDimension.objects.only("scenario_id").filter(pk=self.pk).first()
            if original and original.scenario_id != self.scenario_id:
                raise ValidationError("Allocation dimension scenario cannot be changed.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.scenario.name}:{self.name}"


class AllocationTarget(models.Model):
    """
    Target bucket inside a dimension (e.g., key=met_coal => 5%).
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

        if self.target_percent is not None and (self.target_percent < 0 or self.target_percent > 1):
            raise ValidationError("target_percent must be between 0 and 1.")

        if self.min_percent is not None and (self.min_percent < 0 or self.min_percent > 1):
            raise ValidationError("min_percent must be between 0 and 1.")

        if self.max_percent is not None and (self.max_percent < 0 or self.max_percent > 1):
            raise ValidationError("max_percent must be between 0 and 1.")

        if self.min_percent is not None and self.max_percent is not None and self.min_percent > self.max_percent:
            raise ValidationError("min_percent cannot be greater than max_percent.")

        if self.pk:
            original = AllocationTarget.objects.only("dimension_id").filter(pk=self.pk).first()
            if original and original.dimension_id != self.dimension_id:
                raise ValidationError("Allocation target dimension cannot be changed.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.dimension.name}:{self.key}"
