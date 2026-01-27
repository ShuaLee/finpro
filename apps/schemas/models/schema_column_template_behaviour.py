from django.db import models

from assets.models.core import AssetType
from formulas.models.formula_definition import FormulaDefinition
from schemas.models.schema_column_template import SchemaColumnTemplate


class SchemaColumnTemplateBehaviour(models.Model):
    """
    Default behavior of a schema column template for a specific asset type.
    """

    template = models.ForeignKey(
        SchemaColumnTemplate,
        on_delete=models.CASCADE,
        related_name="behaviours"
    )

    asset_type = models.ForeignKey(
        AssetType,
        on_delete=models.CASCADE,
        related_name="column_template_behaviors",
    )

    source = models.CharField(
        max_length=20,
        choices=[
            ("formula", "Formula"),
            ("holding", "Holding"),
            ("asset", "Asset"),
            ("user", "User Input"),
            ("constant", "Constant"),
        ],
    )

    formula_definition = models.ForeignKey(
        FormulaDefinition,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        help_text="Used when source=formula"
    )

    source_field = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Used when source=holding or source=asset",
    )

    constant_value = models.DecimalField(
        max_digits=30,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Used when source=constant",
    )

    class Meta:
        unique_together = ("template", "asset_type")
