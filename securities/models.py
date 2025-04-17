from django.db import models
from django.core.exceptions import ValidationError
from portfolio.models import Portfolio
from django.utils import timezone
from decimal import Decimal, InvalidOperation
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
    default_schema = models.ForeignKey('StockPortfolioSchema', null=True, blank=True, on_delete=models.SET_NULL, related_name='default_for_portfolios')

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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.initialize_default_schema()

    def __str__(self):
        return f"Stock Portfolio for {self.portfolio.profile.user.email}"

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
    last_price = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    previous_close = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    open_price = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    day_high = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    day_low = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)

    # 52-week range
    fifty_two_week_high = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    fifty_two_week_low = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)

    # Volume
    average_volume = models.BigIntegerField(null=True, blank=True)
    average_volume_10d = models.BigIntegerField(null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)

    # Valuation
    market_cap = models.BigIntegerField(null=True, blank=True)
    beta = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    pe_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    forward_pe = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    price_to_book = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    # Dividends
    dividend_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    dividend_yield = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    payout_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
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

            self.last_price = parse_decimal(info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose'))
            self.previous_close = parse_decimal(info.get('previousClose'))
            self.open_price = parse_decimal(info.get('open'))
            self.day_high = parse_decimal(info.get('dayHigh'))
            self.day_low = parse_decimal(info.get('dayLow'))

            self.fifty_two_week_high = parse_decimal(info.get('fiftyTwoWeekHigh'))
            self.fifty_two_week_low = parse_decimal(info.get('fiftyTwoWeekLow'))

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
    is_deletable = models.BooleanField(default=True)

    class Meta:
        unique_together = ('stock_portfolio', 'name')

    def save(self, *args, **kwargs):
        # Enforce is_deletable rules based on schema name
        if self.name == "Basic":
            if self.pk is not None:  # Existing "Basic" schema
                original = StockPortfolioSchema.objects.get(pk=self.pk)
                if original.is_deletable != False:
                    raise ValidationError(
                        "Cannot change 'is_deletable' for the 'Basic' schema from its original value of False.")
                self.is_deletable = False  # Lock to False
            else:
                self.is_deletable = False  # New "Basic" schema, set to False
        else:
            if self.pk is not None:  # Existing non-"Basic" schema
                original = StockPortfolioSchema.objects.get(pk=self.pk)
                if original.is_deletable != True:
                    raise ValidationError(
                        "Cannot change 'is_deletable' for non-'Basic' schemas from its original value of True.")
                self.is_deletable = True  # Lock to True
            else:
                self.is_deletable = True  # New non-"Basic" schema, set to True

        # Enforce one active schema rule
        if self.is_active:
            StockPortfolioSchema.objects.filter(
                stock_portfolio=self.stock_portfolio,
                is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
        else:
            active_schemas = StockPortfolioSchema.objects.filter(
                stock_portfolio=self.stock_portfolio,
                is_active=True
            )
            if active_schemas.count() == 1 and active_schemas.first().pk == self.pk:
                raise ValidationError(
                    "Cannot deactivate the only active schema. At least one schema must remain active.")

        super().save(*args, **kwargs)

        # Post-save check: Ensure at least one schema is active
        if not StockPortfolioSchema.objects.filter(stock_portfolio=self.stock_portfolio, is_active=True).exists():
            # Fallback: Activate the "Basic" schema if it exists, or the first schema
            basic_schema = StockPortfolioSchema.objects.filter(
                stock_portfolio=self.stock_portfolio,
                name="Basic"
            ).first()
            if basic_schema:
                basic_schema.is_active = True
                basic_schema.save()
            else:
                first_schema = StockPortfolioSchema.objects.filter(
                    stock_portfolio=self.stock_portfolio
                ).first()
                if first_schema:
                    first_schema.is_active = True
                    first_schema.save()
                else:
                    raise ValidationError(
                        "No schemas available to activate. At least one schema must exist and be active.")

    def __str__(self):
        return f"{self.name} ({self.stock_portfolio})"


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


class TickerHistory(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    old_ticker = models.CharField(max_length=10)
    changed_at = models.DateTimeField(auto_now_add=True)