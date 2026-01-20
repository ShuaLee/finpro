from django.core.exceptions import ValidationError
from django.db import models


class MasterConstraint(models.Model):
    """
    Defines a reusable, global constraint template.
    Used to initialize SchemaConstraint records for new SchemaColumns.
    """

    name = models.CharField(max_length=50)
    label = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

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

    # Typed defaults
    default_string = models.CharField(max_length=255, blank=True, null=True)
    default_decimal = models.DecimalField(
        max_digits=20, decimal_places=8, null=True, blank=True
    )
    default_integer = models.IntegerField(null=True, blank=True)

    min_decimal = models.DecimalField(
        max_digits=20, decimal_places=8, null=True, blank=True
    )
    max_decimal = models.DecimalField(
        max_digits=20, decimal_places=8, null=True, blank=True
    )

    class Meta:
        ordering = ["applies_to", "label"]
        unique_together = ("applies_to", "name")

    def __str__(self):
        return f"[{self.applies_to}] {self.label} ({self.name})"


class SchemaConstraint(models.Model):
    """
    Defines a validation / formatting rule for a SchemaColumn.
    All values are stored in typed fields only.
    """

    column = models.ForeignKey(
        "SchemaColumn",
        on_delete=models.CASCADE,
        related_name="constraints_set",
    )

    name = models.CharField(max_length=50)
    label = models.CharField(max_length=100)

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
    )

    # ------------------
    # Typed values
    # ------------------
    value_string = models.CharField(max_length=255, null=True, blank=True)
    value_decimal = models.DecimalField(
        max_digits=20, decimal_places=8, null=True, blank=True
    )
    value_integer = models.IntegerField(null=True, blank=True)

    min_decimal = models.DecimalField(
        max_digits=20, decimal_places=8, null=True, blank=True
    )
    max_decimal = models.DecimalField(
        max_digits=20, decimal_places=8, null=True, blank=True
    )

    min_integer = models.IntegerField(null=True, blank=True)
    max_integer = models.IntegerField(null=True, blank=True)

    is_editable = models.BooleanField(default=True)

    class Meta:
        unique_together = ("column", "name")

    # -------------------------------------------------
    # String representation
    # -------------------------------------------------
    def __str__(self):
        return (
            f"{self.column.identifier}.{self.name}"
            f" = {self.get_typed_value()}"
        )

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------
    def clean(self):
        super().clean()

        if (
            SchemaConstraint.objects.exclude(pk=self.pk)
            .filter(column=self.column, name=self.name)
            .exists()
        ):
            raise ValidationError(
                f"Constraint '{self.name}' already exists for this column."
            )

        value_fields = [
            self.value_string,
            self.value_decimal,
            self.value_integer,
        ]

        if sum(v is not None for v in value_fields) > 1:
            raise ValidationError(
                "Only one typed value field may be set."
            )

        if self.applies_to == "integer":
            if self.value_integer is None:
                raise ValidationError(
                    "Integer constraint requires value_integer."
                )
            if self.min_integer is not None and self.value_integer < self.min_integer:
                raise ValidationError("Value below minimum.")
            if self.max_integer is not None and self.value_integer > self.max_integer:
                raise ValidationError("Value above maximum.")

        if self.applies_to == "decimal":
            if self.name == "decimal_places" and self.value_decimal is None:
                raise ValidationError(
                    "Decimal constraint requires value_decimal.")
            if self.min_decimal is not None and self.value_decimal < self.min_decimal:
                raise ValidationError("Value below minimum.")
            if self.max_decimal is not None and self.value_decimal > self.max_decimal:
                raise ValidationError("Value above maximum.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        from schemas.services.schema_constraint_manager import (
            SchemaConstraintManager
        )

        SchemaConstraintManager._refresh_scv_if_needed(self.column)

    # -------------------------------------------------
    # Typed access API (THIS IS THE ONLY PUBLIC API)
    # -------------------------------------------------
    def get_typed_value(self):
        if self.applies_to == "integer":
            return self.value_integer
        if self.applies_to == "decimal":
            return self.value_decimal
        return self.value_string

    def get_typed_min(self):
        if self.applies_to == "integer":
            return self.min_integer
        if self.applies_to == "decimal":
            return self.min_decimal
        return None

    def get_typed_max(self):
        if self.applies_to == "integer":
            return self.max_integer
        if self.applies_to == "decimal":
            return self.max_decimal
        return None
