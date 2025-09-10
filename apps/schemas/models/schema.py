from django.db import models
from core.types import DomainType
from portfolios.models.subportfolio import SubPortfolio
from assets.models.holding import Holding
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.utils import normalize_constraints


class Schema(models.Model):
    """
    A Schema defines the structure of data for a subportfolio + account type.
    Example: Stock Self-Managed Schema vs Stock Managed Schema.
    """
    subportfolio = models.ForeignKey(
        SubPortfolio,
        on_delete=models.CASCADE,
        related_name="schemas",
    )
    domain_type = models.CharField(
        max_length=20,
        choices=DomainType.choices,
        db_index=True,
    )
    account_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Specific account type within this domain (e.g. stock_self, stock_managed)."
    )
    name = models.CharField(max_length=255)
    schema_type = models.CharField(max_length=50, default="default")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("subportfolio", "account_type")

    def __str__(self):
        return f"{self.name} ({self.subportfolio} - {self.account_type})"


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
        ],
    )
    source = models.CharField(
        max_length=20,
        choices=[
            ("holding", "Holding"),
            ("asset", "Asset"),
            ("calculated", "Calculated"),
            ("custom", "Custom"),
        ],
    )
    source_field = models.CharField(max_length=100, null=True, blank=True)

    # For calculated columns
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

    # Constraints (JSON, normalized in clean())
    constraints = models.JSONField(default=dict, blank=True)
    display_order = models.PositiveIntegerField(default=0)

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
