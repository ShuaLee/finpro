from datetime import datetime
from decimal import Decimal
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
import logging

logger = logging.getLogger(__name__)


class Schema(models.Model):
    # GenericForeignKey to reference sub-portfolios (e.g., StockPortfolio)
    sub_portfolio_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='schemas',
        limit_choices_to={'app_label': 'stock_portfolio',
                          'model__in': ['stockportfolio']}
    )
    sub_portfolio_object_id = models.PositiveIntegerField()
    base_asset_portfolio = GenericForeignKey(
        'sub_portfolio_content_type', 'sub_portfolio_object_id')

    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('sub_portfolio_content_type',
                           'sub_portfolio_object_id', 'name'),)

    def __str__(self):
        return self.name
    """
    def get_structured_holdings(self, account, holding_model, holding_field='stockholdings'):

        Generic method to get structured holdings for any account and holding model.
        :param account: Instance of an account model (e.g., SelfManagedAccount).
        :param holding_model: Model class for holdings (e.g., StockHolding, CryptoHolding).
        :param holding_field: Related name for holdings on account (e.g., 'stockholdings').

        schema_columns = list(self.columns.all())
        holdings = getattr(account, holding_field).select_related(
            'asset').prefetch_related('column_values')

        columns = [
            {
                "id": col.id,
                "name": col.name,
                "data_type": col.data_type,
                "source": col.source,
                "source_field": col.source_field
            }
            for col in schema_columns
        ]

        rows = []
        for holding in holdings:
            row_values = []
            for col in schema_columns:
                value_obj = holding.column_values.filter(column=col).first()
                if not value_obj:
                    value_obj, created = SchemaColumnValue.objects.get_or_create(
                        holding=holding,
                        column=col,
                        defaults={"value": None}
                    )
                    if created:
                        # Generic asset (e.g. Stock, Crypto)
                        if col.cource == 'asset':
                            value_obj.value = str(
                                getattr(holding.asset, col.source_field, None))
                        elif col.source == 'holding':
                            value_obj.value = str(
                                getattr(holding, col.source_field, None))
                        value_obj.save()
                row_values.append({
                    "column_id": col.id,
                    "value_id": value_obj.id,
                    "value": value_obj.value,
                    "is_edited": value_obj.is_edited if col.source == 'asset' else False
                })

            rows.append({
                "holding_id": holding.id,
                "values": row_values
            })

        return {
            "columns": columns,
            "rows": rows
        }
    """
    """
    def delete(self, *args, **kwargs):
        schemas = Schema.objects.filter(portfolio=self.base_asset_portfolio)
        if schemas.count() <= 1:
            raise ValidationError("Cannot delete the last remaining schema.")
        super().delete(*args, **kwargs)
    """


class SchemaColumn(models.Model):
    DATA_TYPES = [
        ('decimal', 'Number'),
        ('string', 'Holding'),
        ('date', 'Date'),
        ('url', 'URL'),
    ]
    SOURCE_TYPE = [
        ('asset', 'Asset'),
        ('holding', 'Holding'),
        ('calculated', 'Calculated'),
        ('custom', 'Custom'),
    ]

    schema = models.ForeignKey(
        Schema,
        on_delete=models.CASCADE,
        related_name='columns'
    )
    name = models.CharField(max_length=100)
    data_type = models.CharField(max_length=10, choices=DATA_TYPES)
    source = models.CharField(max_length=20, choices=SOURCE_TYPE)
    source_field = models.CharField(max_length=100, blank=True, null=True)
    formula = models.TextField(blank=True, null=True)
    editable = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.source})"


class SchemaColumnValue(models.Model):
    # Generic content type for holdings (e.g. StockHolding, CryptoHolding, etc.)
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        limit_choices_to={'app_label__in': ['stock_portfolio', 'crypto']}
    )
    object_id = models.PositiveIntegerField()
    holding = GenericForeignKey('content_type', 'object_id')
    column = models.ForeignKey(
        SchemaColumn,
        on_delete=models.CASCADE,
        related_name='values'
    )
    value = models.TextField(blank=True, null=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        unique_together = ('content_type', 'object_id', 'column')

    def __str__(self):
        return f"{self.holding} | {self.column.name} = {self.value}"

    def validate_value(self, value):
        if value is None:
            return
        data_type = self.column.data_type
        try:
            if data_type == 'decimal':
                decimal_value = Decimal(str(value).strip())
                if self.column.source == 'holding' and self.column.source_field == 'shares':
                    decimal_value = decimal_value.quantize(
                        Decimal('0.0001'), rounding='ROUND_HALF_UP')
                    if len(str(abs(decimal_value).quantize(Decimal('1'))).split('.')[0]) > 11:
                        raise ValueError("Too many digits for shares")
                return decimal_value
            elif data_type == 'date':
                datetime.strptime(value, '%Y-%m-%d')
            elif data_type == 'url':
                URLValidator()(value)
        except (ValueError, TypeError, ValidationError) as e:
            logger.error(
                f"Validation failed for value '{value}' (data_type={data_type}): {str(e)}")
            raise ValidationError(
                f"Invalid value for {self.column.source_field or 'value'}: {value}"
            )
        return value

    def reset_to_default(self):
        if self.column.source == 'asset':
            default_value = getattr(
                self.holding.asset, self.column.source_field, None)
            self.is_edited = False
        elif self.column.source == 'holding':
            default_value = getattr(
                self.holding, self.column.source_field, None)
            self.is_edited = False
        else:
            default_value = None
            self.is_edited = False
        self.value = str(default_value) if default_value is not None else None
        super().save()
        logger.debug(
            f"Reset SchemaColumnValue {self.id}, value={self.value}, is_edited={self.is_edited}")

    def save(self, *args, **kwargs):
        if 'value' in kwargs.get('update_fields', []) or not self.pk:
            validated_value = self.validate_value(self.value)
            if self.column.data_type == 'decimal':
                self.value = str(validated_value)
        super().save(*args, **kwargs)
        logger.debug(
            f"Saved SchemaColumnValue {self.id}, value={self.value}, is_edited={self.is_edited}")
