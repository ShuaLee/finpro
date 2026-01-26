from django.db import models

from assets.models.core import AssetType
from formulas.models.formula_definition import FormulaDefinition
from schemas.models.schema_column import SchemaColumn


class SchemaColumnAssetBehaviour(models.Model):
    """
    Asset-type-specific behavior for a SchemaColumn.
    """

    column = models.ForeignKey(
        SchemaColumn,
        on_delete=models.CASCADE,
        related_name="asset_behaviors",
    )

    asset_type = models.ForeignKey(
        AssetType,
        on_delete=models.CASCADE,
        related_name="schema_column_behaviors",
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
    )

    source_field = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    constant_value = models.DecimalField(
        max_digits=30,
        decimal_places=10,
        null=True,
        blank=True,
    )

    is_override = models.BooleanField(
        default=False,
        help_text="True if user overrode system default.",
    )

    class Meta:
        unique_together = ("column", "asset_type")
