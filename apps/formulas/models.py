from django.db import models
from django.conf import settings
from django.utils.text import slugify
from schemas.models.schema import Schema
import re


def to_snake_case(value: str) -> str:
    value = slugify(value)  # "Cool Ratio" -> "cool-ratio"
    return re.sub(r'[-\s]+', '_', value)  # "cool-ratio" -> "cool_ratio"


class Formula(models.Model):
    key = models.SlugField(
        max_length=100,
        help_text="Stable identifier for this formula, e.g. 'pe_ratio', 'unrealized_gain'"
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    schema = models.ForeignKey(
        Schema,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="formulas",
        help_text="If null, this is a global/system formula. Otherwise, scoped to schema."
    )

    # Expression in terms of other source_fields
    expression = models.TextField(
        help_text="Expression using other column source_fields, e.g. '(price - purchase_price) * quantity'"
    )

    dependencies = models.JSONField(
        default=list,
        blank=True,
        help_text="List of source_fields this formula depends on"
    )

    decimal_places = models.PositiveSmallIntegerField(
        choices=[
            (0, "0 (whole numbers)"),
            (2, "2 (cents)"),
            (4, "4 (fx/crypto standard)"),
            (8, "8 (crypto max precision)")
        ],
        null=True,
        blank=True,
        help_text="Explicit precision for calculated results"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    is_system = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["key"],
                condition=models.Q(is_system=True),
                name="unique_system_formula_key"
            ),
            models.UniqueConstraint(
                fields=["schema", "key"],
                condition=models.Q(is_system=False),
                name="unique_schema_formula_key"
            ),
        ]

    def clean(self):
        super().clean()

        # --- Base validations ---
        if not self.key:
            raise ValueError("Formula must have a stable key.")
        if not self.expression:
            raise ValueError("Formula must define an expression.")
        if not isinstance(self.dependencies, list):
            raise ValueError("Formula dependencies must be a list.")
        for dep in self.dependencies:
            if not isinstance(dep, str):
                raise ValueError(
                    f"Invalid dependency '{dep}', must be a string.")

        # --- Enforce schema scoping rules ---
        if self.is_system and self.schema is not None:
            raise ValueError(
                "System formulas must not be tied to a schema (schema must be NULL).")
        if not self.is_system and self.schema is None:
            raise ValueError("Non-system formulas must be tied to a schema.")

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = to_snake_case(self.title)
        else:
            self.key = to_snake_case(self.key)
        self.full_clean()  # ✅ ensure clean() rules are enforced
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.key})"
