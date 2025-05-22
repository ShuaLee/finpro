from django.core.exceptions import ValidationError
from django.db import models
import logging

logger = logging.getLogger(__name__)


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

    title = models.CharField(max_length=100)
    data_type = models.CharField(max_length=10, choices=DATA_TYPES)
    source = models.CharField(max_length=20, choices=SOURCE_TYPE)
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
