from django.core.exceptions import ValidationError
from django.db import models

from core.types import get_account_type_choices
from assets.models.holding import Holding
from schemas.constraints import CONSTRAINT_TEMPLATES
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.utils import normalize_constraints

from decimal import Decimal


class Schema(models.Model):
    """
    Universal schema definition for a given account_type.
    Example: Stock Self-Managed Schema vs Stock Managed Schema.
    Shared across all accounts of the same type.
    """
    portfolio = models.ForeignKey(
        "portfolios.Portfolio",
        on_delete=models.CASCADE,
        related_name="schemas"
    )

    account_type = models.CharField(
        max_length=50,
        db_index=True,
        choices=get_account_type_choices(),
        help_text="Specific account type this schema applies to (e.g., equity_self, crypto_wallet)."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # One schema per account_type per portfolio
        unique_together = ("portfolio", "account_type")
        ordering = ["account_type"]

    def __str__(self):
        return f"Schema ({self.account_type})"


class SchemaColumn(models.Model):
    """
    Defines a column in a Schema (system, custom, or calculated).
    """

    schema = models.ForeignKey(
        "Schema",
        on_delete=models.CASCADE,
        related_name="columns",
    )
    title = models.CharField(max_length=255)
    identifier = models.SlugField(max_length=100, db_index=True)

    data_type = models.CharField(
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

    source = models.CharField(
        max_length=20,
        choices=[
            ("holding", "Holding"),
            ("asset", "Asset"),
            ("formula", "Formula"),
            ("custom", "Custom"),
        ],
    )

    source_field = models.CharField(max_length=100, null=True, blank=True)

    formula = models.ForeignKey(
        "formulas.Formula",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="schema_columns",
    )

    # Meta flags
    is_editable = models.BooleanField(default=True)
    is_deletable = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)

    # Constraints (JSON, normalized is clean())
    constraints = models.JSONField(default=dict, blank=True)
    display_order = models.PositiveBigIntegerField(default=0)

    class Meta:
        unique_together = ("schema", "identifier")
        ordering = ["display_order", "id"]

    def __str__(self):
        return f"{self.title} ({self.schema.name})"

    # -------------------------------
    # Normalization
    # -------------------------------
    def clean(self):
        if self.constraints:
            self.constraints = normalize_constraints(self.constraints)
        super().clean()

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)

        # 🔑 Create SCVs automatically for all existing holdings when new column is added
        if is_new:
            SchemaColumnValueManager.ensure_for_column(self)


class SchemaColumnValue(models.Model):
    """
    Stores the actual value for a given column + holding.
    Example: Quantity = 10, Price = 100.
    """

    column = models.ForeignKey(
        SchemaColumn,
        on_delete=models.CASCADE,
        related_name="values",
    )
    holding = models.ForeignKey(
        Holding,
        on_delete=models.CASCADE,
        related_name="schema_values",
    )

    value = models.TextField(blank=True, null=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        unique_together = ("column", "holding")

    def __str__(self):
        return f"{self.column.title} = {self.value} ({self.holding})"


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
