from django.db import models
from django.core.exceptions import ValidationError
from assets.models.asset import Holding
from core.types import DomainType
from portfolios.models.subportfolio import SubPortfolio


class Schema(models.Model):
    subportfolio = models.ForeignKey(
        SubPortfolio, on_delete=models.CASCADE, related_name="schemas")
    account_type = models.CharField(max_length=20, choices=DomainType.choices)
    name = models.CharField(max_length=100)
    schema_type = models.CharField(max_length=20, choices=DomainType.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("subportfolio", "account_type")


class SchemaColumn(models.Model):
    """
    Represents a column in a schema.
    Columns define attributes for holdings/accounts and can be:
    - asset-based,
    - holding-based,
    - calculated (via formula/template),
    - custom.
    """

    schema = models.ForeignKey(
        "schemas.Schema",
        on_delete=models.CASCADE,
        related_name="columns"
    )

    formula = models.ForeignKey(
        "formulas.Formula",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Direct formula if this is a custom calculated column"
    )

    title = models.CharField(max_length=100)

    identifier = models.SlugField(
        max_length=100,
        blank=False,
        null=False,
        help_text="Stable internal key used for referencing this column in formulas. Auto-generated for custom columns.",
    )

    data_type = models.CharField(max_length=20, choices=[
        ("decimal", "Number"),
        ("string", "Text"),
        ("date", "Date"),
        ("datetime", "Datetime"),
        ("time", "Time"),
        ("url", "URL"),
    ])
    source = models.CharField(max_length=20, choices=[
        ("asset", "Asset"),
        ("holding", "Holding"),
        ("calculated", "Calculated"),
        ("custom", "Custom"),
    ])
    source_field = models.CharField(max_length=100, blank=True, null=True)

    is_editable = models.BooleanField(default=True)
    is_deletable = models.BooleanField(default=True)
    is_system = models.BooleanField(
        default=False, help_text="Whether this is a system default column"
    )

    constraints = models.JSONField(default=dict, blank=True)

    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.source})"

    def clean(self):
        super().clean()

        if not self.identifier:
            raise ValidationError(
                "SchemaColumn.identifier must be set explicitly (use SchemaGenerator).")


class SchemaColumnValue(models.Model):
    """
    Represents a value for a specific column in an account or holding.
    Uses GenericForeignKey for flexible linking.
    """
    column = models.ForeignKey(
        SchemaColumn, on_delete=models.CASCADE, related_name='values')

    holding = models.ForeignKey(
        Holding,
        on_delete=models.CASCADE,
        related_name="schema_values",
        null=True,
        blank=True,
    )

    value = models.TextField(blank=True, null=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        unique_together = ("column", "holding")
        # You don’t really need conditional constraints anymore,
        # because holding is always required.

    def __str__(self):
        return f"{self.holding} - {self.column.title}: {self.value}"

    def get_value(self):
        """
        Return the stored SCV value.
        """
        return self.value

    def save(self, *args, **kwargs):
        from schemas.services.schema_column_value_manager import SchemaColumnValueManager
        manager = SchemaColumnValueManager(self)
        manager.apply_rules()
        super().save(*args, **kwargs)
