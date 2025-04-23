from django.db import models
from django.utils import timezone
from portfolio.models import Asset, BaseAssetPortfolio
from datetime import datetime
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
        Gets data from yfinance. This logic should be moved later?
        """
        ticker_obj = yf.Ticker(self.ticker)
        
        if not force_update and self.last_updated:
            time_diff = timezone.now() - self.last_updated
            if time_diff.days < 1:
                logger.info(f"Using cached data for {self.ticker}")
                return

        try:
            info = ticker_obj.info
            if not info or 'symbol' not in info:
                logger.warning(f"No valid info for {self.ticker}")
                return
            
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
        
        except Exception as e:
            logger.error(f"Failed to fetch data for {self.ticker}: {e}")
        
    @classmethod
    def create_from_ticker(cls, ticker):
        ticker = ticker.upper()
        instance = cls(ticker=ticker)

        try:
            instance.fetch_yfinance_data()
            instance.save()
            return instance
        except ValueError as e:
            logger.error(f"Stock creation failed for {ticker}: {e}")
            return None

    def save(self, *args, **kwargs):
        if self.ticker:
            self.ticker = self.ticker.upper()
        super().save(*args, **kwargs)

class StockHolding(models.Model):
    stock_account = models.ForeignKey(SelfManagedAccount, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, null=True, on_delete=models.SET_NULL)
    ticker = models.CharField(max_length=10)
    shares = models.DecimalField(max_digits=15, decimal_places=4)
    purchase_price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('stock_account', 'ticker')

    def __str__(self):
        return f"{self.ticker} ({self.shares} shares)"