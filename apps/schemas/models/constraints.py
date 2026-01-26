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
                raise ValidationError("default_integer is required.")
            if self.default_decimal is not None or self.default_string is not None:
                raise ValidationError("Only default_integer may be set.")

        elif self.applies_to == self.AppliesTo.DECIMAL:
            if self.default_decimal is None:
                raise ValidationError("default_decimal is required.")
            if self.default_integer is not None or self.default_string is not None:
                raise ValidationError("Only default_decimal may be set.")

        elif self.applies_to == self.AppliesTo.STRING:
            if self.default_string is None:
                raise ValidationError("default_string is required.")
            if self.default_integer is not None or self.default_decimal is not None:
                raise ValidationError("Only default_string may be set.")


class SchemaConstraint(models.Model):
    """
    Concrete constraint attached to a SchemaColumn.

    Stores the enforced value derived from a MasterConstraint.
    """

    column = models.ForeignKey(
        "schemas.SchemaColumn",
        on_delete=models.CASCADE,
        related_name="constraints",
    )

    name = models.SlugField(
        max_length=100,
        help_text="Constraint identifier (matches MasterConstraint.name).",
    )

    label = models.CharField(
        max_length=255,
    )

    class Source(models.TextChoices):
        SYSTEM = "system", "System"
        USER = "user", "User"

    source = models.CharField(
        max_length=10,
        choices=Source.choices,
        default=Source.SYSTEM,
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

    def clean(self):
        super().clean()

        if self.applies_to == MasterConstraint.AppliesTo.INTEGER:
            if self.value_integer is None:
                raise ValidationError("value_integer is required.")
            if self.value_decimal is not None or self.value_string is not None:
                raise ValidationError("Only value_integer may be set.")

            if self.min_integer is not None and self.value_integer < self.min_integer:
                raise ValidationError(
                    f"{self.value_integer} < minimum {self.min_integer}")
            if self.max_integer is not None and self.value_integer > self.max_integer:
                raise ValidationError(
                    f"{self.value_integer} > maximum {self.max_integer}")

        elif self.applies_to == MasterConstraint.AppliesTo.DECIMAL:
            if self.value_decimal is None:
                raise ValidationError("value_decimal is required.")
            if self.value_integer is not None or self.value_string is not None:
                raise ValidationError("Only value_decimal may be set.")

            if self.min_decimal is not None and self.value_decimal < self.min_decimal:
                raise ValidationError(
                    f"{self.value_decimal} < minimum {self.min_decimal}")
            if self.max_decimal is not None and self.value_decimal > self.max_decimal:
                raise ValidationError(
                    f"{self.value_decimal} > maximum {self.max_decimal}")

        elif self.applies_to == MasterConstraint.AppliesTo.STRING:
            if self.value_string is None:
                raise ValidationError("value_string is required.")
            if self.value_integer is not None or self.value_decimal is not None:
                raise ValidationError("Only value_string may be set.")

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
