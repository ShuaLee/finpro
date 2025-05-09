from decimal import Decimal
from django.core.exceptions import ValidationError
from rest_framework import serializers
from .models import StockPortfolio, SelfManagedAccount, SchemaColumnValue, SchemaColumn, StockHolding
import logging

logger = logging.getLogger(__name__)

"""

class SchemaColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemaColumn
        fields = ['id', 'name', 'data_type',
                  'source', 'source_field', 'editable']


class SchemaColumnValueSerializer(serializers.ModelSerializer):
    reset = serializers.BooleanField(
        write_only=True, required=False, default=False)

    class Meta:
        model = SchemaColumnValue
        fields = ['id', 'stock_holding', 'column',
                  'value', 'is_edited', 'reset']
        read_only_fields = ['stock_holding', 'column', 'is_edited']

    def validate_value(self, value):
        # Validate the value against the column's data type.
        column = self.instance.column if self.instance else SchemaColumn.objects.get(
            id=self.initial_data.get('column'))
        try:
            if column.data_type == 'decimal':
                decimal_value = Decimal(str(value).strip())
                if column.source == 'holding' and column.source_field == 'shares':
                    decimal_value = decimal_value.quantize(
                        Decimal('0.0001'), rounding='ROUND_HALF_UP')
                    if len(str(abs(decimal_value).quantize(Decimal('1'))).split('.')[0]) > 11:
                        raise ValueError("Too many digits for shares")
                return str(decimal_value)
            elif column.data_type == 'date':
                from datetime import datetime
                datetime.strptime(value, '%Y-%m-%d')
            elif column.data_type == 'url':
                from django.core.validators import URLValidator
                URLValidator()(value)
            # 'string' type needs no validation
        except (ValueError, TypeError, ValidationError) as e:
            logger.error(
                f"Validation failed for value '{value}' (data_type={column.data_type}): {str(e)}")
            raise serializers.ValidationError(
                f"Invalid value for {column.source_field or 'value'}: {value}"
            )
        return value

    def update(self, instance, validated_data):
        if validated_data.get('reset'):
            instance.reset_to_default()
        else:
            new_value = validated_data.get('value', instance.value)
            if new_value != instance.value:
                if instance.column.source == 'holding' and instance.column.source_field:
                    # Update StockHolding first
                    try:
                        if instance.column.source_field == 'shares':
                            instance.stock_holding.shares = Decimal(
                                str(new_value).strip())
                        elif instance.column.source_field == 'purchase_price':
                            instance.stock_holding.purchase_price = Decimal(
                                str(new_value).strip())
                        instance.stock_holding.save()
                        instance.value = new_value  # Sync SchemaColumnValue with StockHolding
                    except (ValueError, TypeError) as e:
                        logger.error(
                            f"Failed to update StockHolding for {instance.column.source_field}: {str(e)}")
                        raise serializers.ValidationError(
                            f"Invalid value for {instance.column.source_field}: {new_value}"
                        )
                else:
                    # For source='stock', update value and set is_edited
                    instance.value = new_value
                    instance.is_edited = True if instance.column.source == 'stock' else False
                instance.save()
                logger.debug(
                    f"Updated SchemaColumnValue {instance.id}, value={new_value}, is_edited={instance.is_edited}")
            else:
                logger.debug(
                    f"No change for SchemaColumnValue {instance.id}, value={new_value}, is_edited={instance.is_edited}")
        return instance


class SelfManagedAccountSerializer(serializers.ModelSerializer):
    active_schema_name = serializers.SerializerMethodField()

    class Meta:
        model = SelfManagedAccount
        fields = ['id', 'name', 'currency', 'broker', 'tax_status',
                  'account_type', 'use_default_schema', 'active_schema', 'active_schema_name']
        read_only_fields = ['id']

    def get_active_schema_name(self, obj):
        return obj.active_schema.name if obj.active_schema else None


class StockHoldingSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockHolding
        fields = ['id', 'stock', 'shares', 'purchase_price']


class StockPortfolioSerializer(serializers.ModelSerializer):
    self_managed_accounts = SelfManagedAccountSerializer(
        many=True, read_only=True)

    class Meta:
        model = StockPortfolio
        fields = ['id', 'created_at', 'self_managed_accounts']
"""