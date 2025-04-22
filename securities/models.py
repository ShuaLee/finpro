from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import datetime
import yfinance as yf
import logging

logger = logging.getLogger(__name__)


def parse_decimal(value):
    try:
        return Decimal(str(value)) if value is not None else None
    except:
        return None


def parse_date(value):
    try:
        return datetime.fromtimestamp(value).date() if value else None
    except:
        return None


class StockPortfolio(models.Model):
    portfolio = models.OneToOneField(
        'portfolio.Portfolio', on_delete=models.CASCADE, related_name='stock_portfolio'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self.create_default_schema()

    def create_default_schema(self):
        schema = StockPortfolioSchema.objects.create(
            stock_portfolio=self,
            name='Default'
        )
        schema.create_default_columns()

    def get_active_schema(self):
        return self.schemas.filter(is_active=True).first()

    def initialize_default_schema(self):
        """Create a non-deletable 'Basic' schema if none exist."""
        if not self.schemas.exists():
            schema = StockPortfolioSchema.objects.create(
                stock_portfolio=self,
                name="Basic",
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
            self.default_schema = schema
            self.save(update_fields=["default_schema"])

    def __str__(self):
        return f"Stock Portfolio for {self.portfolio.profile.user.email}"


class Stock(models.Model):
    id = models.AutoField(primary_key=True)
    ticker = models.CharField(max_length=10, unique=True)
    short_name = models.CharField(max_length=100, blank=True, null=True)
    long_name = models.CharField(max_length=200, blank=True, null=True)
    is_etf = models.BooleanField(default=False)
    currency = models.CharField(max_length=10, blank=True)
    exchange = models.CharField(max_length=50, blank=True, null=True)
    quote_type = models.CharField(max_length=50, blank=True, null=True)
    market = models.CharField(max_length=50, blank=True, null=True)

    # Price-related data
    last_price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    previous_close = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    open_price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    day_high = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    day_low = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)

    # 52-week range
    fifty_two_week_high = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    fifty_two_week_low = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)

    # Volume
    average_volume = models.BigIntegerField(null=True, blank=True)
    average_volume_10d = models.BigIntegerField(null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)

    # Valuation
    market_cap = models.BigIntegerField(null=True, blank=True)
    beta = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True)
    pe_ratio = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    forward_pe = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    price_to_book = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)

    # Dividends
    dividend_rate = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    dividend_yield = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    payout_ratio = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    ex_dividend_date = models.DateField(null=True, blank=True)

    # Company Profile
    sector = models.CharField(max_length=100, null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    full_time_employees = models.IntegerField(null=True, blank=True)
    long_business_summary = models.TextField(null=True, blank=True)

    # Timestamps
    last_updated = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.ticker

    def fetch_yfinance_data(self, force_update=False):
        if not force_update and self.last_updated:
            time_diff = timezone.now() - self.last_updated
            if time_diff.days < 1:
                logger.info(f"Using cached data for {self.ticker}")
                return

        ticker_obj = yf.Ticker(self.ticker)

        try:
            info = ticker_obj.info
            if not info or 'symbol' not in info:
                logger.warning(f"No valid info for {self.ticker}")
                return

            self.short_name = info.get('shortName')
            self.long_name = info.get('longName')
            self.is_etf = info.get('quoteType', '').upper() == 'ETF'
            self.currency = info.get('currency')
            self.exchange = info.get('exchange')
            self.quote_type = info.get('quoteType')
            self.market = info.get('market')

            self.last_price = parse_decimal(info.get('currentPrice') or info.get(
                'regularMarketPrice') or info.get('previousClose'))
            self.previous_close = parse_decimal(info.get('previousClose'))
            self.open_price = parse_decimal(info.get('open'))
            self.day_high = parse_decimal(info.get('dayHigh'))
            self.day_low = parse_decimal(info.get('dayLow'))

            self.fifty_two_week_high = parse_decimal(
                info.get('fiftyTwoWeekHigh'))
            self.fifty_two_week_low = parse_decimal(
                info.get('fiftyTwoWeekLow'))

            self.average_volume = info.get('averageVolume')
            self.average_volume_10d = info.get('averageDailyVolume10Day')
            self.volume = info.get('volume')

            self.market_cap = info.get('marketCap')
            self.beta = parse_decimal(info.get('beta'))
            self.pe_ratio = parse_decimal(info.get('trailingPE'))
            self.forward_pe = parse_decimal(info.get('forwardPE'))
            self.price_to_book = parse_decimal(info.get('priceToBook'))

            self.dividend_rate = parse_decimal(info.get('dividendRate'))
            self.dividend_yield = parse_decimal(info.get('dividendYield'))
            self.payout_ratio = parse_decimal(info.get('payoutRatio'))
            self.ex_dividend_date = parse_date(info.get('exDividendDate'))

            self.sector = info.get('sector')
            self.industry = info.get('industry')
            self.website = info.get('website')
            self.full_time_employees = info.get('fullTimeEmployees')
            self.long_business_summary = info.get('longBusinessSummary')

            self.last_updated = timezone.now()
            self.save()

            logger.info(f"Stock {self.ticker} updated successfully.")

        except Exception as e:
            logger.error(f"Failed to fetch data for {self.ticker}: {e}")


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
    stock = models.ForeignKey('Stock', null=True, on_delete=models.SET_NULL)
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

### ------------------------------ Stock Portfolio Schema ------------------------------ ###


class StockPortfolioSchema(models.Model):
    stock_portfolio = models.ForeignKey(
        StockPortfolio, on_delete=models.CASCADE, related_name='schemas')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def create_default_columns(self):
        default_columns = [
            {"title": "Ticker", "source": "stock.ticker",
                "editable": False, "value_type": "text", "is_deletable": False},
            {"title": "Company Name", "source": "stock.long_name",
                "editable": True, "value_type": "text", "is_deletable": True},
            {"title": "Shares", "source": "holding.shares",
                "editable": True, "value_type": "number", "is_deletable": True},
            {"title": "Price", "source": "stock.price",
                "editable": True, "value_type": "number", "is_deletable": True},
            {"title": "Total Value", "source": "calculated.total_value",
                "editable": False, "value_type": "number", "is_deletable": True},
        ]
        for col in default_columns:
            SchemaColumn.objects.create(schema=self, **col)


class SchemaColumn(models.Model):
    COLUMN_CATEGORY_CHOICES = [
        ('custom', 'Custom'),
        ('stock', 'Stock Info'),
        ('holding', 'Holding Info'),
        ('calculated', 'Calculated'),
    ]

    STOCK_SOURCE_CHOICES = [
        # Price
        ('last_price', 'Last Price'),
        ('previous_close', 'Previous Close'),
        ('open_price', 'Open Price'),
        ('day_high', 'Day High'),
        ('day_low', 'Day Low'),
        ('fifty_two_week_high', '52-Week High'),
        ('fifty_two_week_low', '52-Week Low'),

        # Volume
        ('volume', 'Volume'),
        ('average_volume', 'Avg Volume (30d)'),
        ('average_volume_10d', 'Avg Volume (10d)'),

        # Valuation
        ('market_cap', 'Market Cap'),
        ('beta', 'Beta'),
        ('pe_ratio', 'P/E Ratio'),
        ('forward_pe', 'Forward P/E'),
        ('price_to_book', 'Price/Book'),

        # Dividends
        ('dividend_rate', 'Dividend Rate'),
        ('dividend_yield', 'Dividend Yield'),
        ('payout_ratio', 'Payout Ratio'),
        ('ex_dividend_date', 'Ex-Dividend Date'),

        # Company Info
        ('sector', 'Sector'),
        ('industry', 'Industry'),
        ('website', 'Website'),
        ('full_time_employees', 'Employees'),

        # Identity
        ('short_name', 'Short Name'),
        ('long_name', 'Long Name'),
        ('currency', 'Currency'),
        ('exchange', 'Exchange'),
        ('quote_type', 'Quote Type'),
        ('market', 'Market'),
    ]

    HOLDING_SOURCE_CHOICES = [
        ('shares', 'Shares Held'),
        ('purchase_price', 'Purchase Price'),
    ]

    CALCULATED_SOURCE_CHOICES = [
        ('total_investment', 'Total Investment'),
        ('dividends', 'Dividends Earned'),
    ]

    SOURCE_VALUE_TYPE_MAP = {
        'last_price': 'number',
        'previous_close': 'number',
        'open_price': 'number',
        'day_high': 'number',
        'day_low': 'number',
        'fifty_two_week_high': 'number',
        'fifty_two_week_low': 'number',
        'volume': 'number',
        'average_volume': 'number',
        'average_volume_10d': 'number',
        'market_cap': 'number',
        'beta': 'number',
        'pe_ratio': 'number',
        'forward_pe': 'number',
        'price_to_book': 'number',
        'dividend_rate': 'number',
        'dividend_yield': 'number',
        'payout_ratio': 'number',
        'ex_dividend_date': 'date',
        'sector': 'text',
        'industry': 'text',
        'website': 'text',
        'full_time_employees': 'number',
        'short_name': 'text',
        'long_name': 'text',
        'currency': 'text',
        'exchange': 'text',
        'quote_type': 'text',
        'market': 'text',
    }

    schema = models.ForeignKey(
        StockPortfolioSchema, on_delete=models.CASCADE, related_name='columns')
    title = models.CharField(max_length=100)
    source = models.CharField(max_length=50, null=True, blank=True)
    editable = models.BooleanField(default=False)
    is_deletable = models.BooleanField(default=True)
    column_type = models.CharField(
        max_length=20, choices=COLUMN_CATEGORY_CHOICES)


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
