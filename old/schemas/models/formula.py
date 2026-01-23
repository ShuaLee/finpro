from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

import ast
import re


IDENTIFIER_REGEX = re.compile(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b")


def to_snake_case(value: str) -> str:
    value = slugify(value)
    return re.sub(r"[-\s]+", "_", value)


class Formula(models.Model):
    """
    A reusable formula used by SchemaColumns.
    """

    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    identifier = models.SlugField(
        max_length=100,
        unique=True,
        help_text="Stable formula identifier (snake_case)."
    )

    expression = models.TextField(
        help_text="Formula expression using column identifiers."
    )

    # Stored only for transparency / admin visibility
    dependencies = models.JSONField(default=list, blank=True)

    decimal_places = models.PositiveSmallIntegerField(null=True, blank=True)

    supported_asset_types = models.ManyToManyField(
        "assets.AssetType",
        blank=True,
        related_name="formulas",
        help_text=(
            "If empty, formula applies to all asset types. "
            "Otherwise, restricted to these asset types."
        ),
    )

    is_system = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ======================================================
    # Validation
    # ======================================================
    def clean(self):
        super().clean()

        if self.is_system and not self.supported_asset_types.exists():
            raise ValidationError(
                "System formulas must explicitly declare supported asset types."
            )

        if not self.expression:
            raise ValidationError("Formula must define an expression.")

        # Extract identifiers from AST
        parsed = ast.parse(self.expression, mode="eval")
        referenced = {
            node.id
            for node in ast.walk(parsed)
            if isinstance(node, ast.Name)
        }

        # Remove numeric literals accidentally parsed as names
        referenced = {r for r in referenced if not r.isdigit()}

        if self.identifier in referenced:
            raise ValidationError("Formula cannot reference itself.")

        # Dependencies must EXACTLY match expression identifiers
        if set(self.dependencies) != referenced:
            raise ValidationError(
                f"Formula dependencies mismatch. "
                f"Expected {sorted(referenced)}, got {self.dependencies}"
            )

    def save(self, *args, **kwargs):
        self.identifier = to_snake_case(self.identifier or self.title)
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Formula({self.identifier})"
