from django.db import models

from assets.models.core import AssetType
from formulas.models.formula import Formula


class DependencyPolicy(models.TextChoices):
    AUTO_EXPAND = "auto_expand", "Auto-expand dependencies"
    STRICT = "strict", "Strict (no auto-create)"


class FormulaDefinition(models.Model):
    """
    Defines the semantic meaning of a formula in a given context.

    Example:
        identifier = "current_value"
        asset_type = equity
        formula = quantity * price
    """

    identifier = models.SlugField(
        max_length=100,
        help_text="Semantic identifier (e.g. current_value)."
    )

    name = models.CharField(
        max_length=100,
        help_text="Display name."
    )

    description = models.TextField(
        blank=True,
        help_text="Optional description of this formula's meaning."
    )

    asset_type = models.ForeignKey(
        AssetType,
        on_delete=models.CASCADE,
        related_name="formula_definitions",
    )

    formula = models.ForeignKey(
        Formula,
        on_delete=models.PROTECT,
        related_name="definitions",
    )

    dependency_policy = models.CharField(
        max_length=20,
        choices=DependencyPolicy.choices,
        default=DependencyPolicy.STRICT,
        help_text="How missing dependencies are handled."
    )

    is_system = models.BooleanField(
        default=False,
        help_text="System-defined and analytics-safe.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["identifier"]
        constraints = [
            models.UniqueConstraint(
                fields=["identifier", "asset_type"],
                name="uniq_formula_definition_per_asset_type"
            )
        ]

    def __str__(self):
        return f"{self.identifier} [{self.asset_type.slug}]"
    