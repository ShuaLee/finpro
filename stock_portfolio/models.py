from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from portfolio.models import Asset, BaseAssetPortfolio
from datetime import date, datetime
from decimal import Decimal
import yfinance as yf
import logging

logger = logging.getLogger(__name__)

# -------------------- HELPER FUNCTIONS -------------------- #

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
        

# -------------------- STOCK PORTFOLIO -------------------- #

class StockPortfolio(BaseAssetPortfolio):
    def __str__(self):
        return f"Stock Portfolio for {self.portfolio.profile.user.email}"
    
# -------------------- STOCK ACCOUNTS -------------------- #

class BaseAccount(models.Model):
    """
    Abstract class for all stock account models.
    """
    stock_portfolio = models.ForeignKey(StockPortfolio, on_delete=models.CASCADE, related_name='%(class)s_set')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
    
    def __str__(self):
        return self.name
    
class SelfManagedAccount(BaseAccount):
    pass

class ManagedAccount(BaseAccount):
    current_value = models.DecimalField(max_digits=12, decimal_places=2)
    invested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    strategy = models.CharField(max_length=100, null=True, blank=True)

# -------------------- STOCK & STOCK HOLDING -------------------- #

class Stock(Asset):
    id = models.AutoField(primary_key=True)
    ticker = models.CharField(max_length=10, unique=True)
    is_custom = models.BooleanField(default=False)

    # Stock data
    short_name = models.CharField(max_length=100, blank=True, null=True)
    long_name = models.CharField(max_length=200, blank=True, null=True)
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
        """
        Gets data from yfinance and updates model fields.
        Returns True if fetch was successful, False otherwise.
        """
        if not force_update and self.last_updated:
            time_diff = timezone.now() - self.last_updated
            if time_diff.days < 1:
                logger.info(f"Using cached data for {self.ticker}")
                return True

        try:
            ticker_obj = yf.Ticker(self.ticker)
            info = ticker_obj.info

            if not isinstance(info, dict) or 'symbol' not in info:
                logger.warning(f"Invalid or missing data for {self.ticker}: {info}")
                return False
            
            self.short_name = info.get('shortName')
            self.long_name = info.get('longName')
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
            return True
        
        except Exception as e:
            logger.error(f"Failed to fetch data for {self.ticker}: {e}", exc_info=False)
            return False
    
    @classmethod
    def create_from_ticker(cls, ticker):
        """
        Creates a Stock instance from a ticker and fetches yfinance data.
        Returns the instance if successful, None otherwise.
        """
        ticker = ticker.upper()
        instance = cls(ticker=ticker)

        if instance.fetch_yfinance_data():
            instance.is_custom = not any([
                instance.short_name, 
                instance.long_name, 
                instance.exchange
            ])
            instance.save()
            return instance
        else:
            instance.is_custom = True
            logger.warning(f"Stock creation failed for {ticker}: No data fetched")
        
        instance.save()
        return instance

    def save(self, *args, **kwargs):
        if self.ticker:
            self.ticker = self.ticker.upper()
        # Prevent redundant fetch during save
        super().save(*args, **kwargs)

class StockHolding(models.Model):
    stock_account = models.ForeignKey(SelfManagedAccount, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, null=True, on_delete=models.SET_NULL)
    shares = models.DecimalField(max_digits=15, decimal_places=4)
    purchase_price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('stock_account', 'stock')

    def __str__(self):
        return f"{self.stock} ({self.shares} shares)"
    
# -------------------- SCHEMA -------------------- #

class Schema(models.Model):
    stock_portfolio = models.ForeignKey(StockPortfolio, on_delete=models.CASCADE, related_name="schemas")
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class SchemaColumn(models.Model):
    DATA_TYPES = [
        ('decimal', 'Number'),
        ('string', 'String'),
        ('date', 'Date'),
        ('url', 'URL'),
    ]
    SOURCE_TYPE = [
        ('stock', 'Stock'),
        ('holding', 'StockHolding'),
        ('custom', 'Custom'),
    ]

    schema = models.ForeignKey(Schema, on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=100)
    data_type = models.CharField(max_length=10, choices=DATA_TYPES)
    source = models.CharField(max_length=20, choices=SOURCE_TYPE)
    source_field = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.source})"
    
class SchemaColumnValue(models.Model):
    stock_holding = models.ForeignKey(StockHolding, on_delete=models.CASCADE, related_name='column_values')
    column = models.ForeignKey(SchemaColumn, on_delete=models.CASCADE, related_name='values')
    value = models.TextField(blank=True, null=True) # Storing values as Text and parse when retreived.

    class Meta:
        unique_together = ('stock_holding', 'column')

    def __str__(self):
        return f"{self.stock_holding} | {self.column.name} = {self.value}"
