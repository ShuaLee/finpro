from django.core.exceptions import ValidationError
from django.db import models

from datetime import date
from decimal import Decimal


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
        DECIMAL = "decimal", "Number"
        STRING = "string", "String"
        PERCENT = "percent", "Percent"
        BOOLEAN = "boolean", "Boolean"
        DATE = "date", "Date"

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

    default_boolean = models.BooleanField(
        null=True,
        blank=True,
    )

    # -------------------------
    # Bounds (optional)
    # -------------------------
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

    default_date = models.DateField(
        null=True,
        blank=True,
    )

    min_date = models.DateField(null=True, blank=True)
    max_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["applies_to", "name"]

    def default_value(self):
        if self.applies_to in ("decimal", "percent"):
            return self.default_decimal

        if self.applies_to == "string":
            return self.default_string

        if self.applies_to == "boolean":
            return self.default_boolean

        if self.applies_to == "date":
            return self.default_date

        return None

    def __str__(self):
        return f"{self.name} ({self.applies_to})"

    # ==========================================================
    # VALIDATION
    # ==========================================================
    def clean(self):
        super().clean()

        if self.applies_to in (self.AppliesTo.DECIMAL, self.AppliesTo.PERCENT):
            if self.default_decimal is None:
                raise ValidationError("default_decimal is required.")
            if any([
                self.default_string,
                self.default_date,
                self.default_boolean,
            ]):
                raise ValidationError("Only default_decimal may be set.")

        elif self.applies_to == self.AppliesTo.STRING:
            if self.default_string is None:
                raise ValidationError("default_string is required.")
            if any([
                self.default_decimal,
                self.default_date,
                self.default_boolean,
            ]):
                raise ValidationError("Only default_string may be set.")

        elif self.applies_to == self.AppliesTo.DATE:
            if self.default_date is None:
                raise ValidationError("default_date is required.")
            if any([
                self.default_decimal,
                self.default_string,
                self.default_boolean,
            ]):
                raise ValidationError("Only default_date may be set.")

        elif self.applies_to == self.AppliesTo.BOOLEAN:
            if self.default_boolean is None:
                raise ValidationError("default_boolean is required.")
            if any([
                self.default_decimal,
                self.default_string,
                self.default_date,
            ]):
                raise ValidationError("Only default_boolean may be set.")


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
    value_date = models.DateField(null=True, blank=True)
    value_boolean = models.BooleanField(null=True, blank=True)

    # -------------------------
    # Bounds snapshot
    # -------------------------
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

    min_date = models.DateField(null=True, blank=True)
    max_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("column", "name")
        ordering = ["column_id", "name"]

    def clean(self):
        super().clean()

        if self.applies_to in (
            MasterConstraint.AppliesTo.DECIMAL,
            MasterConstraint.AppliesTo.PERCENT,
        ):
            if self.value_decimal is None:
                raise ValidationError("value_decimal is required.")
            if any([
                self.value_string,
                self.value_date,
                self.value_boolean,
            ]):
                raise ValidationError("Only value_decimal may be set.")

            if self.min_decimal is not None and self.value_decimal < self.min_decimal:
                raise ValidationError(
                    f"{self.value_decimal} < minimum {self.min_decimal}"
                )
            if self.max_decimal is not None and self.value_decimal > self.max_decimal:
                raise ValidationError(
                    f"{self.value_decimal} > maximum {self.max_decimal}"
                )

        elif self.applies_to == MasterConstraint.AppliesTo.STRING:
            if self.value_string is None:
                raise ValidationError("value_string is required.")
            if any([
                self.value_decimal,
                self.value_date,
                self.value_boolean,
            ]):
                raise ValidationError("Only value_string may be set.")

        elif self.applies_to == MasterConstraint.AppliesTo.DATE:
            if self.value_date is None:
                raise ValidationError("value_date is required.")
            if self.min_date and self.value_date < self.min_date:
                raise ValidationError(
                    f"{self.value_date} < minimum {self.min_date}"
                )
            if self.max_date and self.value_date > self.max_date:
                raise ValidationError(
                    f"{self.value_date} > maximum {self.max_date}"
                )

        elif self.applies_to == MasterConstraint.AppliesTo.BOOLEAN:
            if self.value_boolean is None:
                raise ValidationError("value_boolean is required.")
            if any([
                self.value_decimal,
                self.value_string,
                self.value_date,
            ]):
                raise ValidationError("Only value_boolean may be set.")

    def __str__(self):
        return f"{self.column.identifier}.{self.name}"

    # ==========================================================
    # VALUE ACCESS
    # ==========================================================
    def get_typed_value(self):
        if self.applies_to in (
            MasterConstraint.AppliesTo.DECIMAL,
            MasterConstraint.AppliesTo.PERCENT,
        ):
            return self.value_decimal
        if self.applies_to == MasterConstraint.AppliesTo.BOOLEAN:
            return self.value_boolean
        if self.applies_to == MasterConstraint.AppliesTo.DATE:
            return self.value_date
        return self.value_string

    # ==========================================================
    # VALIDATION (USER INPUT)
    # ==========================================================
    def validate(self, raw_value):
        """
        Validate a user-provided value against this constraint.
        Raises ValidationError if invalid.
        """

        if raw_value in (None, "", "None"):
            return  # allow empty; higher-level logic decides if required

        # ---------------- DECIMAL / PERCENT ----------------
        if self.applies_to in ("decimal", "percent"):
            try:
                value = Decimal(str(raw_value))
            except Exception:
                raise ValidationError(f"'{raw_value}' is not a valid number.")

            if self.min_decimal is not None and value < self.min_decimal:
                raise ValidationError(
                    f"Value {value} is less than minimum {self.min_decimal}."
                )

            if self.max_decimal is not None and value > self.max_decimal:
                raise ValidationError(
                    f"Value {value} is greater than maximum {self.max_decimal}."
                )

            return

        # ---------------- STRING ----------------
        if self.applies_to == "string":
            value = str(raw_value)

            if self.name == "max_length":
                max_len = int(self.value_string)
                if len(value) > max_len:
                    raise ValidationError(
                        f"Length {len(value)} exceeds maximum {max_len}."
                    )

            if self.name == "enum":
                # enum resolution is handled elsewhere (you already do this)
                return

            return

        # ---------------- BOOLEAN ----------------
        if self.applies_to == "boolean":
            val = str(raw_value).strip().lower()
            if val not in ("true", "false", "1", "0", "yes", "no"):
                raise ValidationError("Invalid boolean value.")
            return

        # ---------------- DATE ----------------
        if self.applies_to == "date":
            try:
                if not isinstance(raw_value, date):
                    value = date.fromisoformat(str(raw_value))
                else:
                    value = raw_value
            except Exception:
                raise ValidationError("Invalid date format (YYYY-MM-DD).")

            if self.min_date and value < self.min_date:
                raise ValidationError(
                    f"Date {value} is before minimum {self.min_date}."
                )

            if self.max_date and value > self.max_date:
                raise ValidationError(
                    f"Date {value} is after maximum {self.max_date}."
                )

            return
