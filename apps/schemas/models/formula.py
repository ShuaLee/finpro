from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from typing import Set

import re


def to_snake_case(value: str) -> str:
    """
    Coverts a title like "unrealizzed Gain %" -> "unrealized_gain"
    """
    value = slugify(value)
    return re.sub(r'[-\s]+', '_', value)


IDENTIFIER_REGEX = re.compile(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b")


class Formula(models.Model):
    """
    A formula attached to a SchemaColumn.

    - Each SchemaColumn may have ONE formula.
    - Formulas compute SCV values using BEDMAS evaluation.
    - Dependencies list must match other SchemaColumn.identifiers.
    """

    # Human metadata
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Internal stable identifier (NOT required to match column.identifier)
    identifier = models.SlugField(
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

    # ======================================================
    # Validation
    # ======================================================
    def clean(self):
        super().clean()

        if not self.identifier:
            raise ValidationError("Formula must have a stable identifier.")

        if not self.expression:
            raise ValidationError("Formula must define an expression.")

        if not isinstance(self.dependencies, list):
            raise ValidationError("Dependencies must be a list.")

        # ---- Normalize + validate dependencies ----
        deps: Set[str] = set()

        for dep in self.dependencies:
            if not isinstance(dep, str):
                raise ValidationError(f"Invalid dependency entry: {dep}")
            deps.add(dep)

        if len(deps) != len(self.dependencies):
            raise ValidationError("Duplicate dependencies are not allowed.")

        # ---- Prevent self-reference ----
        if self.identifier in deps:
            raise ValidationError(
                "Formula cannot depend on itself."
            )

        # ---- Validate expression references ----
        referenced = set(IDENTIFIER_REGEX.findall(self.expression))

        # Remove numeric literals
        referenced = {
            token for token in referenced
            if not token.isdigit()
        }

        unknown = referenced - deps
        if unknown:
            raise ValidationError(
                f"Expression references undeclared dependencies: {sorted(unknown)}"
            )

    # ======================================================
    # Save
    # ======================================================
    def save(self, *args, **kwargs):
        self.identifier = to_snake_case(self.identifier or self.title)
        self.full_clean()
        super().save(*args, **kwargs)

    # ======================================================
    # String representation
    # ======================================================
    def __str__(self):
        return f"Formula({self.identifier})"

    class Meta:
        verbose_name = "Schema Formula"
        verbose_name_plural = "Schema Formulas"
