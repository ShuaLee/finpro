from django.core.exceptions import ValidationError
from django.db import models

from core.types import get_account_type_choices
from assets.models.holding import Holding
from schemas.services.schema_column_value_manager import SchemaColumnValueManager


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
    display_order = models.PositiveBigIntegerField(default=0)

    class Meta:
        unique_together = ("schema", "identifier")
        ordering = ["display_order", "id"]

    def __str__(self):
        return f"{self.title} ({self.schema.account_type})"

    # -------------------------------
    # Normalization
    # -------------------------------
    def clean(self):
        super().clean()

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        if not is_new:
            old = SchemaColumn.objects.get(pk=self.pk)
            immutable_fields = ["data_type",
                                "source", "source_field", "formula"]
            for field in immutable_fields:
                if getattr(old, field) != getattr(self, field):
                    raise ValidationError(
                        f"Field '{field}' cannot be changed after creation."
                    )

        # ✅ Validate before writing to DB
        self.full_clean()

        super().save(*args, **kwargs)

        # 🔑 On creation only: create constraints and holding values
        if is_new:
            from schemas.services.schema_constraint_manager import SchemaConstraintManager
            from schemas.services.schema_column_value_manager import SchemaColumnValueManager
            SchemaConstraintManager.create_from_master(self)
            SchemaColumnValueManager.ensure_for_column(self)

    def delete(self, *args, **kwargs):
        """
        Override delete to automatically resequence display_order
        of remaining columns in the same schema.
        """
        schema = self.schema
        deleted_order = self.display_order

        # Delete this column first
        super().delete(*args, **kwargs)

        # Shift down the remaining columns
        schema.columns.filter(display_order__gt=deleted_order).update(
            display_order=models.F("display_order") - 1
        )


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


"""
CONSTRAINTS
"""
