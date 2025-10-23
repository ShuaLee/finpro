from django.core.exceptions import ValidationError
from django.db import models

from decimal import Decimal


class MasterConstraint(models.Model):
    """
    Defines a reusable, global constraint template.
    Used to initialize SchemaConstraint records for new SchemaColumns.
    """

    # Core metadata
    name = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    # Data type this constraint applies to
    applies_to = models.CharField(
        max_length=20,
        choices=[
            ("string", "String"),
            ("decimal", "Decimal"),
            ("integer", "Integer"),
            ("date", "Date"),
            ("boolean", "Boolean"),
            ("url", "URL"),
        ],
        db_index=True,
    )

    # Default configuration values
    default_value = models.CharField(max_length=100, blank=True, null=True)
    min_limit = models.CharField(max_length=100, blank=True, null=True)
    max_limit = models.CharField(max_length=100, blank=True, null=True)

    # Whether this can be edited by users
    is_editable = models.BooleanField(default=True)

    # Active flag — allows soft-disable of deprecated templates
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["applies_to", "label"]
        unique_together = ("applies_to", "name")

    def __str__(self):
        return f"[{self.applies_to}] {self.label} ({self.name})"
    

class SchemaConstraint(models.Model):
    """
    Defines a validation rule for a SchemaColumn.
    Each constraint stores its own allowed range (min/max).
    """

    column = models.ForeignKey(
        "SchemaColumn",
        on_delete=models.CASCADE,
        related_name="constraints_set",
    )

    # Machine-readable key (e.g., "max_length", "decimal_places")
    name = models.CharField(max_length=50)

    # Human-friendly name (e.g., "Max Length", "Decimal Places")
    label = models.CharField(max_length=100)

    # Constraint value (e.g., 255, 4, or None)
    value = models.CharField(max_length=100, null=True, blank=True)

    # Optional range limits for numeric/date constraints
    min_limit = models.CharField(max_length=100, null=True, blank=True)
    max_limit = models.CharField(max_length=100, null=True, blank=True)

    # Data type that this constraint applies to
    applies_to = models.CharField(
        max_length=20,
        choices=[
            ("string", "String"),
            ("decimal", "Decimal"),
            ("integer", "Integer"),
            ("date", "Date"),
            ("boolean", "Boolean"),
            ("url", "URL"),
        ],
        blank=True,
        null=True,
    )

    # Whether this constraint can be adjusted by users
    is_editable = models.BooleanField(default=True)

    class Meta:
        unique_together = ("column", "name")

    def __str__(self):
        return f"{self.column.identifier}.{self.label} = {self.value}"

    # -----------------------------------------
    # Validation Logic
    # -----------------------------------------
    def clean(self):
        # Enforce unique constraint per column
        if (
            SchemaConstraint.objects.exclude(id=self.id)
            .filter(column=self.column, name=self.name)
            .exists()
        ):
            raise ValidationError(
                f"Constraint '{self.name}' already exists for this column."
            )

        # If value is blank, skip validation
        if self.value in [None, "", "None"]:
            return super().clean()

        # Validate numeric constraints
        try:
            numeric_value = Decimal(self.value)
        except Exception:
            # Only check numeric validity for numeric constraints
            if self.applies_to in ("integer", "decimal"):
                raise ValidationError(
                    f"{self.label} must be a numeric value, got '{self.value}'."
                )
            return super().clean()

        # Enforce min/max range if applicable
        if self.min_limit not in [None, "", "None"]:
            if numeric_value < Decimal(self.min_limit):
                raise ValidationError(
                    f"{self.label} cannot be below {self.min_limit}."
                )
        if self.max_limit not in [None, "", "None"]:
            if numeric_value > Decimal(self.max_limit):
                raise ValidationError(
                    f"{self.label} cannot exceed {self.max_limit}."
                )

        super().clean()
