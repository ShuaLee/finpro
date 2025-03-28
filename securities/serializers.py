from rest_framework import serializers
from django.db import IntegrityError, DataError
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import yfinance as yf
from .models import Stock, StockHolding, StockTag, StockPortfolio, SelfManagedAccount, CustomStockHolding


class StockTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockTag
        fields = ['id', 'name', 'arent']


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ['ticker', 'currency']


class StockHoldingSerializer(serializers.ModelSerializer):
    stock = StockSerializer()
    price = serializers.SerializerMethodField()
    total_investment = serializers.SerializerMethodField()
    dividends = serializers.SerializerMethodField()
    stock_tags = StockTagSerializer(many=True)
    custom_data = serializers.JSONField()

    class Meta:
        model = StockHolding
        fields = [
            'stock', 'shares', 'purchase_price', 'stock_tags',
            'price', 'total_investment', 'dividends', 'custom_data'
        ]

    def get_price(self, obj):
        custom_cols = self.context.get('custom_columns', {})
        price_data = custom_cols.get('price', {})
        if price_data.get('override') and price_data.get('value') is not None:
            return Decimal(str(price_data['value']))
        data = obj.stock.fetch_yfinance_data(['price'])
        price = data.get('price')
        return Decimal(str(price)) if price is not None else None

    def get_total_investment(self, obj):
        price = self.get_price(obj)
        return price * obj.shares if price is not None else None

    def get_dividends(self, obj):
        custom_cols = self.context.get('custom_columns', {})
        div_data = custom_cols.get('dividends', {})
        if div_data.get('override') and div_data.get('value') is not None:
            return Decimal(str(div_data['value']))
        data = obj.stock.fetch_yfinance_data(['dividends'])
        dividends = data.get('dividends')
        return Decimal(str(dividends)) if dividends is not None else None


class StockHoldingCreateSerializer(serializers.ModelSerializer):
    ticker = serializers.CharField(write_only=True)
    confirmed = serializers.BooleanField(write_only=True, default=False)

    def validate_ticker(self, value):
        ticker = value.upper()
        max_length = Stock._meta.get_field('ticker').max_length
        if len(ticker) > max_length:
            raise serializers.ValidationError(
                f"Ticker '{ticker}' is too long. Maximum length is {max_length} characters."
            )
        return ticker

    def create(self, validated_data):
        ticker = validated_data.pop('ticker')
        confirmed = validated_data.pop('confirmed')
        stock_account = self.context['stock_account']
        holding_data = {k: v for k, v in validated_data.items(
        ) if k in ['shares', 'purchase_price', 'custom_data']}

        # Check for duplicates
        if StockHolding.objects.filter(stock_account=stock_account, stock__ticker=ticker).exists() or \
           CustomStockHolding.objects.filter(stock_account=stock_account, ticker=ticker).exists():
            raise serializers.ValidationError(
                f"Ticker '{ticker}' is already in this account.")

        # Check if ticker is verified
        yf_ticker = yf.Ticker(ticker)
        try:
            info = yf_ticker.info
            if info and 'symbol' in info and info['symbol'] == ticker:
                stock, _ = Stock.objects.get_or_create(ticker=ticker)
                stock.fetch_yfinance_data()
                return StockHolding.objects.create(
                    stock_account=stock_account,
                    stock=stock,
                    **holding_data
                )
        except Exception:
            if not confirmed:
                raise serializers.ValidationError(
                    f"Stock '{ticker}' does not exist on Yahoo Finance. "
                    "Confirm with 'confirmed=True' to add it as a custom holding."
                )

        # Unverified case
        return CustomStockHolding.objects.create(
            stock_account=stock_account,
            ticker=ticker,
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


class CustomStockHoldingSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    total_investment = serializers.SerializerMethodField()
    dividends = serializers.SerializerMethodField()
    custom_data = serializers.JSONField()

    class Meta:
        model = CustomStockHolding
        fields = [
            'ticker', 'shares', 'purchase_price',
            'price', 'total_investment', 'dividends', 'custom_data'
        ]

    def get_price(self, obj):
        custom_cols = self.context.get('custom_columns', {})
        price_data = custom_cols.get('price', {})
        if price_data.get('override') and price_data.get('value') is not None:
            return Decimal(str(price_data['value']))
        return None  # No live data for custom tickers

    def get_total_investment(self, obj):
        price = self.get_price(obj)
        return price * obj.shares if price is not None else None

    def get_dividends(self, obj):
        custom_cols = self.context.get('custom_columns', {})
        div_data = custom_cols.get('dividends', {})
        if div_data.get('override') and div_data.get('value') is not None:
            return Decimal(str(div_data['value']))
        return None


class SelfManagedAccountSerializer(serializers.ModelSerializer):
    stock_holdings = StockHoldingSerializer(
        many=True, read_only=True, source='stockholding_set')
    custom_stock_holdings = CustomStockHoldingSerializer(
        many=True, read_only=True, source='customstockholding_set')

    class Meta:
        model = SelfManagedAccount
        fields = ['id', 'account_name', 'created_at',
                  'stock_holdings', 'custom_stock_holdings']


class StockPortfolioSerializer(serializers.ModelSerializer):
    self_managed_accounts = SelfManagedAccountSerializer(
        many=True, read_only=True)

    class Meta:
        model = StockPortfolio
        fields = ['id', 'created_at', 'self_managed_accounts']
