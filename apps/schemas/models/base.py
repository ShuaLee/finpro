from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models
from assets.constants import ASSET_SCHEMA_CONFIG


class Schema(models.Model):
    """
    Abstract base class for all schema types (e.g., stock, metal).
    Represents a collection of schema columns linked to a portfolio.
    """

    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    @property
    def portfolio_relation_name(self):
        """
        Must be implemented by subclasses to return the name of the portfolio FK field.
        """
        raise NotImplementedError(
            "Subclasses must define portfolio_relation_name")

    def delete(self, *args, **kwargs):
        """
        Prevent deletion if this is the last schema for the portfolio.
        """
        portfolio = getattr(self, self.portfolio_relation_name)
        if portfolio.schemas.count() <= 1:
            raise PermissionDenied(
                "Cannot delete the last schema for this portfolio.")
        super().delete(*args, **kwargs)


class SchemaColumn(models.Model):
    """
    Abstract base for columns in a schema.
    Contains metadata such as type, source, and editability.
    """

    DATA_TYPES = [
        ('decimal', 'Number'),
        ('integer', 'Integer'),
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
    source_field = models.CharField(max_length=100, blank=True, null=True)
    decimal_spaces = models.PositiveSmallIntegerField(blank=True, null=True)
    formula = models.TextField(blank=True, null=True)
    editable = models.BooleanField(default=True)
    is_deletable = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.title} ({self.source})"

    def clean(self):
        """
        Validate source_field and source compatibility.
        """
        if self.source in ['asset', 'holding'] and not self.source_field:
            raise ValidationError(
                "source_field is required for asset or holding sources.")

        asset_type = getattr(self.__class__, 'ASSET_TYPE', None)
        if not asset_type:
            raise ValidationError(
                "ASSET_TYPE must be defined on SchemaColumn subclasses.")

        if self.source in ['asset', 'holding', 'calculated']:
            valid_fields = list(ASSET_SCHEMA_CONFIG.get(
                asset_type, {}).get(self.source, {}).keys())
            if self.source_field not in valid_fields:
                raise ValidationError(
                    f"Invalid source_field '{self.source_field}' for {asset_type}. "
                    f"Valid options: {sorted(valid_fields)}"
                )

    def delete(self, *args, **kwargs):
        """
        Prevent deletion if this column is mandatory.
        """
        if not self.is_deletable:
            raise PermissionDenied(
                "This column is mandatory and cannot be deleted.")
        super().delete(*args, **kwargs)


class SchemaColumnValue(models.Model):
    """
    Represents the value for a schema column for a given holding.
    """

    value = models.TextField(blank=True, null=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def get_portfolio_from_column(self):
        raise NotImplementedError("Must implement in subclass")

    def get_portfolio_from_holding(self):
        raise NotImplementedError("Must implement in subclass")

    def clean(self):
        """
        Validate portfolio consistency and type correctness.
        """
        if self.column and self.holding:
            if self.get_portfolio_from_column() != self.get_portfolio_from_holding():
                raise ValidationError(
                    "Column and holding belong to different portfolios.")

        if self.is_edited and self.value in [None, '']:
            raise ValidationError(
                f"Cannot mark '{self.column.title}' as edited with empty value.")

        if self.is_edited and self.value is not None:
            expected_type = self.column.data_type
            try:
                if expected_type == 'decimal':
                    float(self.value)
                elif expected_type == 'integer':
                    int(self.value)
                elif expected_type == 'string':
                    str(self.value)
            except (ValueError, TypeError):
                raise ValidationError(
                    f"Invalid type for '{self.column.title}'. Expected {expected_type}.")
