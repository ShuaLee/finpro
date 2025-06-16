from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models
from assets.constants import ASSET_SCHEMA_CONFIG
from stock_portfolio.models import StockPortfolio
import logging

logger = logging.getLogger(__name__)

# ----------------------------- Abstract Classes ------------------------------ #

class Schema(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class SchemaColumn(models.Model):
    DATA_TYPES = [
        ('decimal', 'Number'),
        ('string', 'Text'),
        ('date', 'Date'),
        ('url', 'URL'),
    ]
    SOURCE_TYPE = [
        ('asset', 'Asset'),
        ('holding', 'Holding'),
        ('calculated', 'Calculated'),
        ('custom', 'Custom'),
    ]

    @classmethod
    def get_source_field_choices(cls):
        asset_type = getattr(cls, 'ASSET_TYPE', None)
        if not asset_type:
            return []
        
        config = ASSET_SCHEMA_CONFIG.get(asset_type, {})
        choices = []
        for source, fields in config.items():
            for source_field in fields:
                label = f"{source} - {source_field.replace('_', ' ').title()}" if source_field else f"{source} - Custom"
                choices.append((source_field, label))
        return choices

    title = models.CharField(max_length=100)
    data_type = models.CharField(max_length=10, choices=DATA_TYPES)
    source = models.CharField(max_length=20, choices=SOURCE_TYPE)
    source_field = models.CharField(max_length=100, blank=True, null=True)
    formula = models.TextField(blank=True, null=True)
    editable = models.BooleanField(default=True)
    is_deletable = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.title} ({self.source})"

    def clean(self):
        if self.source in ['asset', 'holding'] and not self.source_field:
            raise ValidationError(
                "source_field is required for asset or holding sources.")
        if self.source == 'calculated' and not self.formula:
            raise ValidationError(
                "formula is required for calculated sources.")
        if self.source == 'custom' and (self.source_field or self.formula):
            raise ValidationError(
                "custom sources should not have source_field or formula.")


class SchemaColumnValue(models.Model):
    value = models.TextField(blank=True, null=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def get_value(self):
        """
        Return the user-edited value or the derived value.
        """
        if self.is_edited:
            return self.value

        # Logic to derive value based on column's source
        column = self.column
        if column.source == 'asset':
            # Fetch from asset (e.g., stock price)
            return getattr(self.holding.asset, column.source_field, None)
        elif column.source == 'holding':
            # Fetch from holding (e.g., quantity)
            return getattr(self.holding, column.source_field, None)
        elif column.source == 'calculated':
            # Evaluate formula (simplified; needs proper implementation)
            return self.evaluate_formula(column.formula)
        return self.value

    def evaluate_formula(self, formula):
        # Placeholder: Implement formula evaluation (e.g., using safe eval or a parser)
        return "0.00"

# ------------------------------ Stock Portfolio ------------------------------ #

class StockPortfolioSchema(Schema):
    stock_portfolio = models.ForeignKey(
        StockPortfolio,
        on_delete=models.CASCADE,
        related_name='schemas'
    )
    
    class Meta:
        unique_together = (('stock_portfolio', 'name'))
    
    def delete(self, *args, **kwargs):
        if self.stock_portfolio.schemas.count() <= 1:
            raise PermissionDenied("Cannot delete the last schema for a Stock Portfolio.")
        super().delete(*args, **kwargs)

class StockPortfolioSC(SchemaColumn):
    ASSET_TYPE = 'stock'

    schema = models.ForeignKey(
        StockPortfolioSchema,
        on_delete=models.CASCADE,
        related_name='columns'
    )
    source_field = models.CharField(
        max_length=100,
        choices=SchemaColumn.get_source_field_choices.__func__(),
        blank=True
    )

    class Meta:
        unique_together = (('schema', 'title'),)

    def __str__(self):
        return f"[{self.schema.stock_portfolio.portfolio.profile}] {self.title} ({self.source})"