from rest_framework import serializers
from django.db import IntegrityError, DataError
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from .models import Stock, StockHolding, StockTag, StockPortfolio, SelfManagedAccount
import yfinance as yf
import logging

logger = logging.getLogger(__name__)


class StockTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockTag
        fields = ['id', 'name', 'parent']


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ['ticker', 'currency', 'is_etf',
                  'dividend_rate', 'dividend_yield']


class StockHoldingSerializer(serializers.ModelSerializer):
    stock = StockSerializer(allow_null=True)
    price = serializers.SerializerMethodField()
    total_investment = serializers.SerializerMethodField()
    dividends = serializers.SerializerMethodField()
    stock_tags = StockTagSerializer(many=True)
    custom_data = serializers.JSONField()

    class Meta:
        model = StockHolding
        fields = [
            'ticker', 'stock', 'shares', 'purchase_price', 'stock_tags',
            'price', 'total_investment', 'dividends', 'custom_data'
        ]

    def to_representation(self, instance):
        # Get custom_columns from the portfolio via context
        portfolio = instance.stock_account.stock_portfolio
        custom_columns = portfolio.custom_columns

        # Default representation
        ret = super().to_representation(instance)

        # Add dynamic fields based on custom_columns
        for column_name, config in custom_columns.items():
            if config.get('visible', True):
                if column_name == 'ticker':
                    ret[column_name] = instance.ticker
                elif column_name == 'shares':
                    ret[column_name] = str(instance.shares)
                elif column_name == 'purchase_price':
                    ret[column_name] = str(
                        instance.purchase_price) if instance.purchase_price else None
                elif column_name == 'price':
                    override = instance.custom_data.get(
                        column_name, {}).get('value')
                    if override is not None and instance.custom_data.get(column_name, {}).get('override', False):
                        ret[column_name] = str(Decimal(override))
                    else:
                        ret[column_name] = str(
                            instance.stock.last_price) if instance.stock and instance.stock.last_price else None
                elif column_name == 'total_investment':
                    override = instance.custom_data.get(
                        column_name, {}).get('value')
                    if override is not None and instance.custom_data.get(column_name, {}).get('override', False):
                        ret[column_name] = str(Decimal(override))
                    else:
                        price = Decimal(ret.get('price', '0')) if ret.get(
                            'price') else Decimal('0')
                        ret[column_name] = str(
                            price * instance.shares) if price else None
                elif column_name == 'dividends':
                    override = instance.custom_data.get(
                        column_name, {}).get('value')
                    if override is not None and instance.custom_data.get(column_name, {}).get('override', False):
                        ret[column_name] = str(Decimal(override))
                    else:
                        if instance.stock:
                            if instance.stock.is_etf:
                                yield_percent = instance.stock.dividend_yield or Decimal(
                                    '0')
                                total_investment = Decimal(ret.get('total_investment', '0')) if ret.get(
                                    'total_investment') else Decimal('0')
                                ret[column_name] = str(
                                    (total_investment * yield_percent) / Decimal('100')) if yield_percent else None
                            else:
                                rate = instance.stock.dividend_rate or Decimal(
                                    '0')
                                ret[column_name] = str(
                                    rate * instance.shares) if rate else None
                        else:
                            ret[column_name] = None

        return ret

    def get_price(self, obj):
        custom_cols = self.context.get('custom_columns', {})
        price_data = custom_cols.get('price', {})
        if price_data.get('override') and price_data.get('value') is not None:
            return Decimal(str(price_data['value']))
        if obj.stock:  # Check if stock exists
            data = obj.stock.fetch_yfinance_data()
            price = data.get('price')
            logger.debug(f"Price for {obj.ticker}: {price}")
            return Decimal(str(price)) if price is not None else None
        return None  # Return None for unverified tickers

    def get_total_investment(self, obj):
        price = self.get_price(obj)
        return price * obj.shares if price is not None else None

    def get_dividends(self, obj):
        custom_cols = self.context.get('custom_columns', {})
        div_data = custom_cols.get('dividends', {})
        if div_data.get('override') and div_data.get('value') is not None:
            return Decimal(str(div_data['value']))
        if obj.stock:
            data = obj.stock.fetch_yfinance_data()
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
    custom_data = serializers.JSONField()

    class Meta:
        model = StockHolding
        fields = ['custom_data']

    def update(self, instance, validated_data):
        instance.shares = validated_data.get('shares', instance.shares)
        instance.purchase_price = validated_data.get(
            'purchase_price', instance.purchase_price)
        instance.custom_data = validated_data.get(
            'custom_data', instance.custom_data)
        instance.save()
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
        holding_data = {k: v for k, v in validated_data.items(
        ) if k in ['shares', 'purchase_price', 'custom_data']}

        # Check for duplicates based on ticker
        if StockHolding.objects.filter(stock_account=stock_account, ticker=ticker).exists():
            raise serializers.ValidationError(
                f"Ticker '{ticker}' is already in this account.")

        # Check if ticker is verified
        stock = None
        yf_ticker = yf.Ticker(ticker)
        try:
            info = yf_ticker.info
            if info and 'symbol' in info and info['symbol'] == ticker:
                stock, _ = Stock.objects.get_or_create(ticker=ticker)
                stock.fetch_yfinance_data()
                stock.refresh_from_db()  # Ensure we get the latest data
                logger.info(
                    f"Created/Updated stock {ticker} with price={stock.last_price}")
        except Exception as e:
            logger.error(f"Error verifying {ticker}: {str(e)}")
            if not confirmed:
                raise serializers.ValidationError(
                    f"Stock '{ticker}' does not exist on Yahoo Finance. "
                    "Confirm with 'confirmed=True' to add it."
                )
            # Stock remains None for unverified tickers

        # Create StockHolding
        return StockHolding.objects.create(
            stock_account=stock_account,
            ticker=ticker,  # Always save the ticker
            stock=stock,    # Link to Stock if verified, otherwise None
            **holding_data
        )

    class Meta:
        model = StockHolding  # Still used for the endpoint, but creates either model
        fields = ['ticker', 'shares', 'confirmed']


class SelfManagedAccountCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelfManagedAccount
        fields = ['account_name']

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
        fields = ['id', 'account_name', 'created_at',
                  'stock_holdings']


class StockPortfolioSerializer(serializers.ModelSerializer):
    self_managed_accounts = SelfManagedAccountSerializer(
        many=True, read_only=True)
    custom_columns = serializers.JSONField()

    class Meta:
        model = StockPortfolio
        fields = ['id', 'created_at',
                  'self_managed_accounts', 'custom_columns']

    def update(self, instance, validated_data):
        instance.custom_columns = validated_data.get(
            'custom_columns', instance.custom_columns)
        instance.save()
        return instance
