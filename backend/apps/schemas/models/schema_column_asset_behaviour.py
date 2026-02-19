from django.core.exceptions import ValidationError
from django.db import models

from assets.models.core import AssetType
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

    formula_identifier = models.SlugField(
        max_length=100,
        null=True,
        blank=True,
        help_text="FormulaDefinition identifier when source=formula.",
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

    def clean(self):
        super().clean()

        if self.source == "holding" and not self.column.is_editable:
            raise ValidationError(
                "Holding-backed columns must be editable."
            )

        if self.source == "formula":
            if not self.formula_identifier:
                raise ValidationError(
                    "formula_identifier is required when source='formula'."
                )
            if self.source_field:
                raise ValidationError(
                    "source_field must be empty when source='formula'."
                )
            if self.constant_value is not None:
                raise ValidationError(
                    "constant_value must be empty when source='formula'."
                )
            return

        if self.source in {"holding", "asset"}:
            if not self.source_field:
                raise ValidationError(
                    "source_field is required when source is holding or asset."
                )
            if self.formula_identifier:
                raise ValidationError(
                    "formula_identifier must be empty when source is holding or asset."
                )
            if self.constant_value is not None:
                raise ValidationError(
                    "constant_value must be empty when source is holding or asset."
                )
            return

        if self.source == "constant":
            if self.constant_value is None:
                raise ValidationError(
                    "constant_value is required when source='constant'."
                )
            if self.formula_identifier or self.source_field:
                raise ValidationError(
                    "formula_identifier and source_field must be empty when source='constant'."
                )
            return

        if self.formula_identifier or self.source_field or self.constant_value is not None:
            raise ValidationError(
                "formula_identifier, source_field, and constant_value must be empty when source='user'."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
