from datetime import datetime
from decimal import Decimal
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from .constants import SOURCE_FIELD_CHOICES, FIELD_DATA_TYPES
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


"""
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

    def delete(self, *args, **kwargs):
        schemas = Schema.objects.filter(portfolio=self.base_asset_portfolio)
        if schemas.count() <= 1:
            raise ValidationError("Cannot delete the last remaining schema.")
        super().delete(*args, **kwargs)

"""
"""
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

    schema = models.ForeignKey(
        Schema,
        on_delete=models.CASCADE,
        related_name='columns'
    )
    name = models.CharField(max_length=100)
    data_type = models.CharField(max_length=10, choices=DATA_TYPES)
    source = models.CharField(max_length=20, choices=SOURCE_TYPE)
    source_field = models.CharField(max_length=100)
    formula = models.TextField(blank=True, null=True)
    editable = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.source})"

    def clean(self):
        super().clean()
        valid_fields = []
        if self.source == 'asset':
            valid_fields = SOURCE_FIELD_CHOICES['asset']['stockportfolio']
        elif self.source == 'holding':
            valid_fields = SOURCE_FIELD_CHOICES['holding']
        elif self.source in ('calculated', 'custom'):
            if self.source_field:
                raise ValidationError(
                    f"source_field must be empty for source '{self.source}'."
                )
            return

        valid_field_names = [f[0] for f in valid_fields]
        if self.source_field not in valid_field_names:
            raise ValidationError(
                f"Invalid source_field '{self.source_field}' for source '{self.source}'. "
                f"Valid options are: {', '.join(valid_field_names)}."
            )

        expected_data_type = FIELD_DATA_TYPES.get(self.source_field)
        if expected_data_type and self.data_type != expected_data_type:
            raise ValidationError(
                f"Data type '{self.data_type}' does not match expected type '{expected_data_type}' "
                f"for source_field '{self.source_field}'."
            )

        # Suggest name based on source_field
        expected_name = next(
            (f[2] for f in valid_fields if f[0] == self.source_field), None)
        if expected_name and self.name != expected_name:
            # Allow custom names, but warn if different
            logger.warning(
                f"SchemaColumn name '{self.name}' differs from expected '{expected_name}' "
                f"for source_field '{self.source_field}'."
            )


class SchemaColumnValue(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={
            'app_label': 'stock_portfolio',
            'model': 'stockholding'
        }
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

    def clean(self):
        super().clean()
        if self.column and self.content_type:
            portfolio_type = self.column.schema.sub_portfolio_content_type.model
            if portfolio_type != 'stockportfolio' or self.content_type.model != 'stockholding':
                raise ValidationError(
                    f"Content type {self.content_type} is invalid for portfolio type '{portfolio_type}'."
                )
            if self.column.source == 'asset' and self.holding:
                asset_ct = ContentType.objects.get_for_model(
                    self.holding.asset)
                valid_asset_models = ['stock', 'customstock']
                if asset_ct.model not in valid_asset_models:
                    raise ValidationError(
                        f"Holding's asset {asset_ct} is invalid for column source 'asset'."
                    )

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
        self.save()
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
"""
