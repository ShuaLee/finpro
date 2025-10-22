from django.db import models

from core.types import get_account_type_choices
from assets.models.holding import Holding
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.utils import normalize_constraints


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
    Defines a validation rule for a schema column.
    """
    column = models.ForeignKey(
        SchemaColumn,
        on_delete=models.CASCADE,
        related_name="constraints_set",
    )

    # Name of the constraint (e.g., 'max_value', 'min_value', 'max_length')
    name = models.CharField(max_length=50)

    # Generic value (can store int, decimal, or string)
    value = models.CharField(max_length=100)

    # Optional: Limit which data_type this applies to
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

    is_system = models.BooleanField(default=False)
    is_editable = models.BooleanField(default=True)

    class Meta:
        unique_together = ("column", "name")

    def __str__(self):
        return f"{self.column.identifier}.{self.name} = {self.value}"
    

"""
🧱 2️⃣ The Professional Upgrade — Structured Constraints
🧠 Core Concept

Introduce a Constraint model that defines per-data-type, per-column rules,
and link it to your SchemaColumn.

This becomes metadata about metadata — just like Django model field attributes (max_length, decimal_places, etc.) but dynamic and database-driven.

🧩 3️⃣ Proposed Models
SchemaConstraint
class SchemaConstraint(models.Model):

    Defines a validation rule for a schema column.

    column = models.ForeignKey(
        "SchemaColumn",
        on_delete=models.CASCADE,
        related_name="constraints_set",
    )

    # Name of the constraint (e.g., 'max_value', 'min_value', 'max_length')
    name = models.CharField(max_length=50)

    # Generic value (can store int, decimal, or string)
    value = models.CharField(max_length=100)

    # Optional: Limit which data_type this applies to
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

    is_system = models.BooleanField(default=False)
    is_editable = models.BooleanField(default=True)

    class Meta:
        unique_together = ("column", "name")

    def __str__(self):
        return f"{self.column.identifier}.{self.name} = {self.value}"

💡 Example Constraints
data_type	name	value	behavior
decimal	decimal_places	4	Rounds/truncates at 4
decimal	max_value	1000000	Value cap
string	max_length	100	Enforces char limit
date	min_date	2000-01-01	Enforces lower bound
integer	max_value	1000	Cap for integer fields
⚙️ 4️⃣ Enforcing Type-Specific Rules

When a value is created or updated (e.g., through SchemaColumnValueManager),
you can automatically enforce constraint logic based on data type:

def enforce_constraints(column, value):
    for c in column.constraints_set.all():
        if c.name == "max_length" and len(str(value)) > int(c.value):
            raise ValidationError(f"{column.title} exceeds max length {c.value}.")
        if c.name == "max_value" and Decimal(value) > Decimal(c.value):
            raise ValidationError(f"{column.title} exceeds max value {c.value}.")
        if c.name == "decimal_places":
            q = Decimal(value).quantize(Decimal("1." + "0" * int(c.value)))
            value = q
    return value


💡 And you can enforce “meta-constraints” — e.g.,
System columns’ constraints are read-only:

if c.is_system and not user.is_admin:
    raise PermissionDenied("Cannot modify system constraint.")

🧠 5️⃣ Constraint Templates per Data Type

You can predefine allowed constraint types for each data_type
so new columns get the right set automatically:

DATA_TYPE_CONSTRAINTS = {
    "string": ["max_length"],
    "decimal": ["max_value", "min_value", "decimal_places"],
    "integer": ["max_value", "min_value"],
    "date": ["min_date", "max_date"],
    "boolean": [],
    "url": ["max_length"],
}


During schema generation:

for constraint_name in DATA_TYPE_CONSTRAINTS.get(column.data_type, []):
    SchemaConstraint.objects.create(
        column=column,
        name=constraint_name,
        value=default_for(constraint_name),
        is_system=column.is_system,
    )
"""