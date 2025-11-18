from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

import re


def to_snake_case(value: str) -> str:
    """
    Coverts a title like "unrealizzed Gain %" -> "unrealized_gain"
    """
    value = slugify(value)
    return re.sub(r'[-\s]+', '_', value)


class Formula(models.Model):
    """
    A formula attached to a SchemaColumn.

    - Each SchemaColumn may have ONE formula.
    - Formulas compute SCV values using BEDMAS evaluation.
    - Dependencies list must match other SchemaColumn.identifiers.
    """

    column = models.OneToOneField(
        "schemas.SchemaColumn",
        on_delete=models.CASCADE,
        related_name="formula",
        help_text="The SchemaColumn whose value will be computed via this formula."
    )

    # Human metadata
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Internal stable identifier (NOT required to match column.identifier)
    key = models.SlugField(
        max_length=100,
        help_text="Stable formula key (auto-normalized to snake_case)."
    )

    # Expression text (e.g., '(last_price - purchase_price) * quantity')
    expression = models.TextField(
        help_text="Formula expression using column identifiers."
    )

    # JSON list of identifiers used in the formula
    dependencies = models.JSONField(
        default=list,
        blank=True,
        help_text="Identifiers of SchemaColumns that this formula depends on."
    )

    # Optional display precision
    decimal_places = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="If set, overrides SchemaColumn constraints for result precision."
    )

    # Whether this formula is system-level (protected)
    is_system = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # =============================================
    # Model Validation
    # =============================================
    def clean(self):
        super().clean()

        if not self.key:
            raise ValidationError("Formula must have a stable key.")

        if not self.expression:
            raise ValidationError("Formula must define an expression.")

        if not isinstance(self.dependencies, list):
            raise ValidationError("Formula dependencies must be a list.")

        for dep in self.dependencies:
            if not isinstance(dep, str):
                raise ValidationError(f"Invalid dependency entry: {dep}")

        # System formulas cannot belong to portfolio schemas
        if self.is_system and self.column.schema.portfolio_id is not None:
            raise ValidationError(
                "System formulas must not be tied to a portoflio schema."
            )

    # =============================================
    # Save Handler
    # =============================================
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = to_snake_case(self.title)
        else:
            self.key = to_snake_case(self.key)
        self.full_clean()
        super().save(*args, **kwargs)

    # =============================================
    # String repr
    # =============================================
    def __str__(self):
        return f"Formula({self.column.identifier} = {self.key})"

    class Meta:
        verbose_name = "Schema Formula"
        verbose_name_plural = "Schema Formulas"
        constraints = [
            # each SchemaColumn may only have 1 formula
            models.UniqueConstraint(
                fields=["column"],
                name="unique_formula_per_column",
            ),
        ]
