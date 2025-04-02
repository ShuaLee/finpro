from django.db import models
from portfolio.models import Portfolio
from django.utils import timezone
from decimal import Decimal, InvalidOperation
import yfinance as yf
import logging

logger = logging.getLogger(__name__)

# Create your models here.


class StockPortfolio(models.Model):
    portfolio = models.OneToOneField(
        'portfolio.Portfolio', on_delete=models.CASCADE, related_name='stock_portfolio'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def get_active_schema(self):
        return self.schemas.filter(is_active=True).first()

    def initialize_default_schema(self):
        """Create a non-deletable 'Basic' schema if none exist."""
        if not self.schemas.exists():
            schema = StockPortfolioSchema.objects.create(
                stock_portfolio=self,
                name="Basic",
                is_active=True,
                is_deletable=False  # Non-deletable
            )
            defaults = [
                {"title": "Ticker", "source": "stock.ticker",
                    "editable": False, "value_type": "text"},
                {"title": "Number of Shares", "source": "holding.shares",
                    "editable": True, "value_type": "number"},
                {"title": "Price", "source": "stock.price",
                    "editable": True, "value_type": "number"},
                {"title": "Total Investment", "source": "calculated.total_investment",
                    "editable": True, "value_type": "number"},
                {"title": "Dividends", "source": "calculated.dividends",
                    "editable": True, "value_type": "number"}
            ]
            for col in defaults:
                SchemaColumn.objects.create(schema=schema, **col)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.initialize_default_schema()

    def __str__(self):
        return f"Stock Portfolio for {self.portfolio.user.email}"

# ------------------------------------------------------------------------------------------- #


class StockTag(models.Model):
    # e.g. "Coal Producer", "Tech", etc.
    name = models.CharField(max_length=100)
    stock_holding = models.ForeignKey(
        'StockHolding', on_delete=models.CASCADE, related_name='stock_tags'
    )

    # Nested sub-tags
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE, related_name='sub_tags'
    )

    def __str__(self):
        return self.name


class Stock(models.Model):
    ticker = models.CharField(max_length=10, unique=True)
    currency = models.CharField(max_length=10, blank=True)
    is_etf = models.BooleanField(default=False)
    stock_exchange = models.CharField(max_length=50, blank=True, null=True)
    dividend_rate = models.DecimalField(
        max_digits=15, decimal_places=4, null=True, blank=True)
    dividend_yield = models.DecimalField(
        max_digits=15, decimal_places=4, null=True, blank=True)
    last_price = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.ticker

    def fetch_yfinance_data(self, force_update=False):
        """
        Fetch data from yfinance and update the model. If force_update=False, use cached data if recent.
        """
        # Check if data is recent (e.g., within 1 day) and not forced.
        if not force_update and self.last_updated:
            time_diff = timezone.now() - self.last_updated
            if time_diff.days < 1:
                logger.info(
                    f"Using cached data for {self.ticker}: price={self.last_price}, rate={self.dividend_rate}, yield={self.dividend_yield}")
                return {
                    'price': self.last_price,
                    'dividend_rate': self.dividend_rate,
                    'dividend_yield': self.dividend_yield,
                    'currency': self.currency,
                    'stock_exchange': self.stock_exchange,
                    'is_etf': self.is_etf,
                }

        ticker = yf.Ticker(self.ticker)
        try:
            info = ticker.info
            if not info or 'symbol' not in info or info['symbol'] != self.ticker.upper():
                logger.warning(f"No valid data for {self.ticker}")
                return {}

            # Update fields based on yfinance data
            self.is_etf = info.get('quoteType') == 'ETF'
            self.currency = info.get('currency')
            self.stock_exchange = info.get('exchange')
            self.last_price = Decimal(str(info.get('currentPrice') or info.get(
                'regularMarketPrice') or info.get('previousClose') or 0))
            self.last_updated = timezone.now()

            # Handle dividends/yield based on ETF status
            if self.is_etf:
                self.dividend_yield = Decimal(
                    # Fraction (e.g., 0.0156)
                    str(info.get('dividendYield', 0) or 0))
                self.dividend_rate = None
            else:
                self.dividend_rate = Decimal(
                    str(info.get('dividendRate', 0) or 0))
                self.dividend_yield = Decimal(
                    # Optional for stocks
                    str(info.get('dividendYield', 0) or 0))

            # Save updated fields
            self.save(update_fields=['is_etf', 'currency', 'stock_exchange',
                      'dividend_rate', 'dividend_yield', 'last_price', 'last_updated'])
            logger.info(
                f"Updated {self.ticker}: price={self.last_price}, dividends={self.dividend_rate}")
            return {
                'price': self.last_price,
                'dividend_rate': self.dividend_rate,
                'dividend_yield': self.dividend_yield,
                'currency': self.currency,
                'stock_exchange': self.stock_exchange,
                'is_etf': self.is_etf,
            }
        except Exception as e:
            logger.error(f"Error fetching data for {self.ticker}: {str(e)}")
            return {}


class StockAccount(models.Model):
    stock_portfolio = models.ForeignKey(
        StockPortfolio, on_delete=models.CASCADE, related_name='stock_accounts'
    )
    account_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True  # Base class for all account types

    def __str__(self):
        return f"{self.account_name} - {self.stock_portfolio}"


class SelfManagedAccount(StockAccount):
    stock_portfolio = models.ForeignKey(
        StockPortfolio, on_delete=models.CASCADE, related_name='self_managed_accounts'
    )
    stocks = models.ManyToManyField(
        'Stock', through='StockHolding', related_name='self_managed_accounts', blank=True
    )


class StockHolding(models.Model):
    stock_account = models.ForeignKey(
        'SelfManagedAccount', on_delete=models.CASCADE)
    stock = models.ForeignKey('Stock', null=True, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=10)
    shares = models.DecimalField(max_digits=15, decimal_places=4)
    purchase_price = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('stock_account', 'ticker')

    def __str__(self):
        return f"{self.ticker} ({self.shares} shares)"

    def sync_values(self):
        """Sync values based on the active schema."""
        schema = self.stock_account.stock_portfolio.get_active_schema()
        if not schema:
            return

        for column in schema.columns.all():
            value_obj, created = self.values.get_or_create(column=column)
            if value_obj.edited:
                continue

            if column.source == 'stock.ticker':
                value_obj.set_value(self.ticker)
            elif column.source == 'holding.shares':
                value_obj.set_value(self.shares)
            elif column.source == 'stock.price' and self.stock:
                value_obj.set_value(self.stock.last_price)
            elif column.source == 'calculated.total_investment':
                price_obj = self.values.filter(column__title='Price').first()
                price = price_obj.get_value() if price_obj else Decimal('0')
                value_obj.set_value(price * self.shares)
            elif column.source == 'calculated.dividends' and self.stock:
                if self.stock.is_etf:
                    yield_percent = self.stock.dividend_yield or Decimal('0')
                    total_obj = self.values.filter(
                        column__title='Total Investment').first()
                    total = total_obj.get_value() if total_obj else Decimal('0')
                    value_obj.set_value(
                        (total * yield_percent) / Decimal('100'))
                else:
                    rate = self.stock.dividend_rate or Decimal('0')
                    value_obj.set_value(rate * self.shares)
            else:  # manual
                if created:
                    value_obj.set_value(
                        0 if column.value_type == 'number' else False if column.value_type == 'boolean' else '')

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.sync_values()


class StockPortfolioSchema(models.Model):
    stock_portfolio = models.ForeignKey(
        StockPortfolio, on_delete=models.CASCADE, related_name='schemas')
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)
    is_deletable = models.BooleanField(default=True)  # New field

    class Meta:
        unique_together = ('stock_portfolio', 'name')

    def save(self, *args, **kwargs):
        if self.is_active:
            StockPortfolioSchema.objects.filter(stock_portfolio=self.stock_portfolio, is_active=True).exclude(
                pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.stock_portfolio})"

# SchemaColumn: Defines columns within a schema


class SchemaColumn(models.Model):
    schema = models.ForeignKey(
        StockPortfolioSchema, on_delete=models.CASCADE, related_name='columns')
    title = models.CharField(max_length=100)
    source = models.CharField(
        max_length=50,
        choices=[
            ('manual', 'Manual Input'),
            ('stock.ticker', 'Stock Ticker'),
            ('holding.shares', 'Shares'),
            ('stock.price', 'Current Price'),
            ('calculated.total_investment', 'Total Investment'),
            ('calculated.dividends', 'Dividends')
        ],
        default='manual'
    )
    editable = models.BooleanField(default=True)
    value_type = models.CharField(
        max_length=10,
        choices=[('text', 'Text'), ('number', 'Number'),
                 ('boolean', 'Boolean')],
        default='text'
    )

    class Meta:
        unique_together = ('schema', 'title')

    def __str__(self):
        return f"{self.title} ({self.schema})"

# HoldingValue: Stores values for each holding based on the active schema


class HoldingValue(models.Model):
    holding = models.ForeignKey(
        'StockHolding', on_delete=models.CASCADE, related_name='values')
    column = models.ForeignKey(SchemaColumn, on_delete=models.CASCADE)
    value_text = models.CharField(max_length=255, null=True, blank=True)
    value_number = models.DecimalField(
        max_digits=15, decimal_places=4, null=True, blank=True)
    value_boolean = models.BooleanField(null=True)
    edited = models.BooleanField(default=False)

    class Meta:
        unique_together = ('holding', 'column')

    def get_value(self):
        if self.column.value_type == 'text':
            return self.value_text
        elif self.column.value_type == 'number':
            return self.value_number
        elif self.column.value_type == 'boolean':
            return self.value_boolean
        return None

    def set_value(self, value):
        if self.column.value_type == 'text':
            self.value_text = str(value) if value is not None else None
            self.value_number = None
            self.value_boolean = None
        elif self.column.value_type == 'number':
            self.value_number = Decimal(
                str(value)) if value is not None else None
            self.value_text = None
            self.value_boolean = None
        elif self.column.value_type == 'boolean':
            self.value_boolean = value in (
                True, 'true', '1', 'yes') if value is not None else None
            self.value_text = None
            self.value_number = None
        self.save()
