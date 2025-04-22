from rest_framework import serializers
from django.db import IntegrityError, DataError
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from datetime import timedelta
from .models import Stock, StockHolding, StockPortfolio, SelfManagedAccount, SchemaColumn, HoldingValue, StockPortfolioSchema
import yfinance as yf
import logging

logger = logging.getLogger(__name__)


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ['ticker', 'currency', 'is_etf',
                  'dividend_rate', 'dividend_yield']


class HoldingValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = HoldingValue
        fields = ['column', 'value_text',
                  'value_number', 'value_boolean', 'edited']

    def to_representation(self, instance):
        value = instance.get_value()
        return {'column': instance.column.title, 'value': value, 'edited': instance.edited}


class StockHoldingSerializer(serializers.ModelSerializer):
    stock = StockSerializer(allow_null=True)
    values = HoldingValueSerializer(many=True, read_only=True)
    price = serializers.SerializerMethodField()
    total_investment = serializers.SerializerMethodField()
    dividends = serializers.SerializerMethodField()

    class Meta:
        model = StockHolding
        fields = ['ticker', 'stock', 'shares', 'purchase_price',
                  'values', 'price', 'total_investment', 'dividends']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['table_data'] = {value['column']: {'value': value['value'], 'edited': value['edited']}
                             for value in ret['values']}
        del ret['values']  # Remove raw values list, keep table_data
        return ret

    def get_price(self, obj):
        # Fetch the 'Price' value from HoldingValue
        price_obj = obj.values.filter(column__title='Price').first()
        if price_obj and price_obj.edited and price_obj.get_value() is not None:
            return Decimal(str(price_obj.get_value()))

        if obj.stock:
            data = obj.stock.fetch_yfinance_data()
            if data:
                price = data.get('last_price')
                logger.debug(f"Price for {obj.ticker}: {price}")
                return Decimal(str(price)) if price is not None else None
            else:
                logger.warning(f"No data returned for stock: {obj.ticker}")

        return None

    def get_total_investment(self, obj):
        price = self.get_price(obj)
        return price * obj.shares if price is not None else None

    def get_dividends(self, obj):
        # Fetch the 'Dividends' value from HoldingValue
        div_obj = obj.values.filter(column__title='Dividends').first()
        if div_obj and div_obj.edited and div_obj.get_value() is not None:
            return Decimal(str(div_obj.get_value()))
        if obj.stock:
            data = obj.stock.fetch_yfinance_data()
            if not data:
                return None  # Avoid NoneType error if data is missing

            total_investment = self.get_total_investment(obj)
            if obj.stock.is_etf and total_investment is not None:
                yield_percent = data.get('dividend_yield')
                if yield_percent is not None:
                    total_dividends = (total_investment *
                                       yield_percent) / Decimal('100')
                    logger.debug(
                        f"ETF {obj.ticker} dividends: yield={yield_percent}%, total={total_dividends}")
                    return total_dividends
            else:
                rate = data.get('dividend_rate')
                if rate is not None:
                    total_dividends = rate * obj.shares
                    logger.debug(
                        f"Stock {obj.ticker} dividends: rate={rate}, total={total_dividends}")
                    return total_dividends
        return None


class StockHoldingUpdateSerializer(serializers.ModelSerializer):
    holding_display = serializers.JSONField()

    class Meta:
        model = StockHolding
        fields = ['shares', 'purchase_price', 'holding_display']

    def validate_holding_display(self, value):
        portfolio = self.instance.stock_account.stock_portfolio
        for title, config in value.items():
            schema_col = next(
                (col for col in portfolio.column_schema if col['title'] == title), None)
            if not schema_col or not schema_col.get('editable', False):
                continue  # Skip non-editable or undefined columns

            new_value = config.get('value')
            value_type = schema_col.get('value_type', 'text')
            if new_value is not None:
                if value_type == 'number':
                    try:
                        Decimal(new_value)
                    except (ValueError, TypeError, InvalidOperation):
                        raise serializers.ValidationError(
                            f"Column '{title}' must be a number.")
                elif value_type == 'boolean':
                    if str(new_value).lower() not in ('true', 'false', '1', '0', 'yes', 'no'):
                        raise serializers.ValidationError(
                            f"Column '{title}' must be a boolean (true/false).")
        return value

    def update(self, instance, validated_data):
        instance.shares = validated_data.get('shares', instance.shares)
        instance.purchase_price = validated_data.get(
            'purchase_price', instance.purchase_price)
        new_display = validated_data.get(
            'holding_display', instance.holding_display)

        portfolio = instance.stock_account.stock_portfolio
        for column in portfolio.column_schema:
            title = column['title']
            if column.get('editable', False) and title in new_display:
                new_value = new_display[title].get('value')
                existing = instance.holding_display.get(title, {})
                if new_value != existing.get('value'):
                    # Cast value to match value_type
                    value_type = column.get('value_type', 'text')
                    if value_type == 'number':
                        new_value = str(Decimal(new_value)
                                        ) if new_value else None
                    elif value_type == 'boolean':
                        new_value = str(new_value).lower() in (
                            'true', '1', 'yes') if new_value else False
                    elif value_type == 'text':
                        new_value = str(new_value) if new_value else None

                    instance.holding_display[title] = {
                        'value': new_value,
                        'edited': True
                    }

        instance.sync_holding_display(save=True)
        return instance


class StockHoldingCreateSerializer(serializers.ModelSerializer):
    ticker = serializers.CharField(write_only=True)
    confirmed = serializers.BooleanField(write_only=True, default=False)
    shares = serializers.DecimalField(max_digits=15, decimal_places=4)

    def validate_ticker(self, value):
        ticker = value.upper()
        max_length = Stock._meta.get_field('ticker').max_length
        if len(ticker) > max_length:
            raise serializers.ValidationError(
                f"Ticker '{ticker}' is too long. Maximum length is {max_length} characters."
            )
        return ticker

    def validate_shares(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Shares cannot be negative. Must be 0 or greater.")
        return value

    def create(self, validated_data):
        ticker = validated_data.pop('ticker')
        confirmed = validated_data.pop('confirmed')
        stock_account = self.context['stock_account']
        holding_data = {k: v for k, v in validated_data.items() if k in [
            'shares', 'purchase_price']}

        if StockHolding.objects.filter(stock_account=stock_account, ticker=ticker).exists():
            raise serializers.ValidationError(
                f"Ticker '{ticker}' is already in this account.")

        stock = None
        yf_ticker = yf.Ticker(ticker)
        try:
            info = yf_ticker.info
            if info and 'symbol' in info and info['symbol'] == ticker:
                stock, _ = Stock.objects.get_or_create(ticker=ticker)
                stock.fetch_yfinance_data()
                stock.refresh_from_db()
                logger.info(
                    f"Created/Updated stock {ticker} with price={stock.last_price}")
        except Exception as e:
            logger.error(f"Error verifying {ticker}: {str(e)}")
            if not confirmed:
                raise serializers.ValidationError(
                    f"Stock '{ticker}' does not exist on Yahoo Finance. Confirm with 'confirmed=True' to add it.")

        holding = StockHolding(
            stock_account=stock_account,
            ticker=ticker,
            stock=stock,
            **holding_data
        )
        holding.save()  # Triggers initial sync with 'edited': False
        return holding

    class Meta:
        model = StockHolding  # Still used for the endpoint, but creates either model
        fields = ['ticker', 'shares', 'confirmed']


class SelfManagedAccountCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelfManagedAccount
        fields = ['account_name']  # Only require account_name for creation

    def create(self, validated_data):
        stock_portfolio = self.context.get('stock_portfolio')
        if not stock_portfolio:
            raise serializers.ValidationError(
                "stock_portfolio is required in context")
        return SelfManagedAccount.objects.create(stock_portfolio=stock_portfolio, **validated_data)


class SelfManagedAccountSerializer(serializers.ModelSerializer):
    stock_holdings = StockHoldingSerializer(
        many=True, read_only=True, source='stockholding_set')

    class Meta:
        model = SelfManagedAccount
        fields = ['id', 'account_name', 'created_at', 'stock_holdings']


class StockPortfolioColumnSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=100)
    source = serializers.ChoiceField(
        choices=[
            ('manual', 'Manual Input'),
            ('stock.ticker', 'Stock Ticker'),
            ('holding.shares', 'Shares'),
            ('holding.purchase_price', 'Purchase Price'),
            ('stock.price', 'Current Price'),
            ('calculated.total_investment', 'Total Investment'),
            ('calculated.dividends', 'Dividends')
        ],
        default='manual'
    )
    editable = serializers.BooleanField(default=True)
    value_type = serializers.ChoiceField(
        choices=[
            ('text', 'Text'),
            ('number', 'Number'),
            ('boolean', 'Boolean')
        ],
        default='text'
    )

    def update(self, instance, validated_data):
        title = validated_data['title']
        source = validated_data['source']
        editable = validated_data['editable']
        value_type = validated_data['value_type']

        existing = next(
            (col for col in instance.column_schema if col['title'] == title), None)
        if existing:
            existing.update(
                {'source': source, 'editable': editable, 'value_type': value_type})
        else:
            instance.column_schema.append({
                'title': title,
                'source': source,
                'editable': editable,
                'value_type': value_type
            })

        instance.save()
        return instance


class SchemaColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemaColumn
        fields = ['title', 'source', 'editable', 'value_type', 'column_type']


class StockPortfolioSchemaSerializer(serializers.ModelSerializer):
    columns = SchemaColumnSerializer(many=True, read_only=True)

    class Meta:
        model = StockPortfolioSchema
        fields = ['id', 'name', 'columns']  # Added is_deletable


class StockPortfolioSerializer(serializers.ModelSerializer):
    self_managed_accounts = SelfManagedAccountSerializer(
        many=True, read_only=True)
    schemas = StockPortfolioSchemaSerializer(
        many=True, read_only=True)  # Updated from column_schema

    class Meta:
        model = StockPortfolio
        fields = ['id', 'created_at', 'self_managed_accounts', 'schemas']

    def update(self, instance, validated_data):
        instance.column_schema = validated_data.get(
            'column_schema', instance.column_schema)
        instance.save()
        return instance


class SchemaColumnAddSerializer(serializers.Serializer):
    """
    title = serializers.CharField(
        max_length=100, required=False, allow_blank=True)
    """
    column_type = serializers.ChoiceField(
        choices=SchemaColumn.COLUMN_CATEGORY_CHOICES)
    source = serializers.CharField(required=False)
    editable = serializers.BooleanField(default=True, required=False)
    value_type = serializers.ChoiceField(
        choices=[('text', 'Text'), ('number', 'Number'),
                 ('boolean', 'Boolean'), ('date', 'Date')],
        default='text',
        required=False
    )

    def validate_value_type(self, value):
        source = self.initial_data.get('source', None)

        if source:
            # Automatically set value_type based on source
            expected_value_type = SchemaColumn.SOURCE_VALUE_TYPE_MAP.get(
                source)

            if expected_value_type and value != expected_value_type:
                raise serializers.ValidationError(
                    f"Value type must be '{expected_value_type}' for the selected source."
                )
            return expected_value_type  # Return the expected value_type if source exists

        # If no source, return the provided value_type (or default to 'text')
        return value or 'text'  # Default to 'text' if not provided

    def validate(self, data):
        column_type = data.get('column_type')
        source = data.get('source')
        value_type = data.get('value_type')

        valid_sources = {
            'stock': dict(SchemaColumn.STOCK_SOURCE_CHOICES),
            'holding': dict(SchemaColumn.HOLDING_SOURCE_CHOICES),
            'calculated': dict(SchemaColumn.CALCULATED_SOURCE_CHOICES),
        }

        if column_type == 'custom' and source:
            raise serializers.ValidationError(
                f"Custom columns cannot have a source. You provided source='{source}'."
            )

        if column_type == 'custom':
            data['title'] = "Custom"
            data['value_type'] = value_type or 'text'
        else:
            if not source:
                raise serializers.ValidationError(
                    f"Source is required for column type '{column_type}'."
                )
            if column_type in valid_sources and source not in valid_sources[column_type]:
                raise serializers.ValidationError(
                    f"Invalid source '{source}' for column type '{column_type}'."
                )
            # Auto-fill title with the source's display name
            data['title'] = valid_sources[column_type][source]
            # Auto-set value_type based on source for non-custom columns, ignoring provided value_type
            data['value_type'] = SchemaColumn.SOURCE_VALUE_TYPE_MAP.get(
                source, 'text')

        return data

    def validate_title(self, value):
        # Allow blank title since it will be auto-filled in validate()
        return value or ""
