from django.core.exceptions import ValidationError
from django.db import models


class MasterConstraint(models.Model):
    """
    System-level constraint definition.

    Defines:
        - constraint name
        - applicable data type
        - default value
        - optional bounds

    MasterConstraints are reused across schemas.
    """

    class AppliesTo(models.TextChoices):
        INTEGER = "integer", "Integer"
        DECIMAL = "decimal", "Decimal"
        STRING = "string", "String"

    name = models.SlugField(
        max_length=100,
        help_text="Constraint identifier (e.g. decimal_places, min_value).",
        unique=True,
    )

    label = models.CharField(
        max_length=255,
        help_text="Human-readable label.",
    )

    applies_to = models.CharField(
        max_length=20,
        choices=AppliesTo.choices,
    )

    # -------------------------
    # Defaults
    # -------------------------
    default_integer = models.IntegerField(
        null=True,
        blank=True,
    )

    default_decimal = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
    )

    default_string = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    # -------------------------
    # Bounds (optional)
    # -------------------------
    min_integer = models.IntegerField(null=True, blank=True)
    max_integer = models.IntegerField(null=True, blank=True)

    min_decimal = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
    )
    max_decimal = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["applies_to", "name"]

    def __str__(self):
        return f"{self.name} ({self.applies_to})"

    # ==========================================================
    # VALIDATION
    # ==========================================================
    def clean(self):
        super().clean()

        if self.applies_to == self.AppliesTo.INTEGER:
            if self.default_integer is None:
                raise ValidationError(
                    "default_integer is required for integer constraints."
                )

        elif self.applies_to == self.AppliesTo.DECIMAL:
            if self.default_decimal is None:
                raise ValidationError(
                    "default_decimal is required for decimal constraints."
                )

        elif self.applies_to == self.AppliesTo.STRING:
            if self.default_string is None:
                raise ValidationError(
                    "default_string is required for string constraints."
                )


class SchemaConstraint(models.Model):
    """
    Concrete constraint attached to a SchemaColumn.

    Stores the enforced value derived from a MasterConstraint.
    """

    column = models.ForeignKey(
        "schemas.SchemaColumn",
        on_delete=models.CASCADE,
        related_name="constraints_set",
    )

    name = models.SlugField(
        max_length=100,
        help_text="Constraint identifier (matches MasterConstraint.name).",
    )

    label = models.CharField(
        max_length=255,
    )

    applies_to = models.CharField(
        max_length=20,
        choices=MasterConstraint.AppliesTo.choices,
    )

    is_editable = models.BooleanField(
        default=False,
        help_text="Whether the user may override this constraint.",
    )

    # -------------------------
    # Typed value storage
    # -------------------------
    value_integer = models.IntegerField(null=True, blank=True)
    value_decimal = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
    )
    value_string = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    # -------------------------
    # Bounds snapshot
    # -------------------------
    min_integer = models.IntegerField(null=True, blank=True)
    max_integer = models.IntegerField(null=True, blank=True)

    min_decimal = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
    )
    max_decimal = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
    )

    class Meta:
        unique_together = ("column", "name")
        ordering = ["column_id", "name"]

    def __str__(self):
        return f"{self.column.identifier}.{self.name}"

    # ==========================================================
    # VALUE ACCESS
    # ==========================================================
    def get_typed_value(self):
        """
        Return the stored value in its proper Python type.
        """
        if self.applies_to == MasterConstraint.AppliesTo.INTEGER:
            return self.value_integer

        if self.applies_to == MasterConstraint.AppliesTo.DECIMAL:
            return self.value_decimal

        return self.value_string
