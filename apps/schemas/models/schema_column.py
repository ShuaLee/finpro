from django.core.exceptions import ValidationError
from django.db import models

from schemas.models.schema import Schema


class SchemaColumn(models.Model):
    """
    Defines a column inside a Schema.
    """

    class Source(models.TextChoices):
        HOLDING = "holding", "Holding"
        ASSET = "asset", "Asset"
        FORMULA = "formula", "Formula"
        CUSTOM = "custom", "Custom"

    class DataType(models.TextChoices):
        STRING = "string", "String"
        DECIMAL = "decimal", "Decimal"
        INTEGER = "integer", "Integer"
        BOOLEAN = "boolean", "Boolean"
        DATE = "date", "Date"
        URL = "url", "URL"

    schema = models.ForeignKey(
        Schema,
        on_delete=models.CASCADE,
        related_name="columns",
    )

    title = models.CharField(max_length=255)

    identifier = models.SlugField(
        max_length=100,
        help_text="Stable identifier used by formulas and analytics.",
    )

    data_type = models.CharField(
        max_length=20,
        choices=DataType.choices,
    )

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
    )

    # Used for holding / asset sources
    source_field = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    # Used only when source == FORMULA
    formula_definition = models.ForeignKey(
        "formulas.FormulaDefinition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="schema_columns",
    )

    is_required = models.BooleanField(
        default=False,
        help_text="Required for analytics / schema completeness.",
    )

    is_editable = models.BooleanField(default=True)
    is_deletable = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)

    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("schema", "identifier")
        ordering = ["display_order", "id"]

    def __str__(self):
        return f"{self.title} ({self.schema.account_type.slug})"

    def clean(self):
        super().clean()

        if self.source == self.Source.FORMULA:
            if not self.formula_definition:
                raise ValidationError(
                    "Formula columns must define a formula_definition."
                )
            if self.source_field:
                raise ValidationError(
                    "source_field must be empty for formula columns."
                )

        elif self.source in (self.Source.HOLDING, self.Source.ASSET):
            if not self.source_field:
                raise ValidationError(
                    f"source_field is required for source '{self.source}'."
                )
            if self.formula_definition:
                raise ValidationError(
                    "formula_definition must be empty unless source='formula'."
                )

        elif self.source == self.Source.CUSTOM:
            if self.source_field or self.formula_definition:
                raise ValidationError(
                    "Custom columns cannot define source_field or formula_definition."
                )
