from django.db import models
from portfolio.models import Portfolio
from django.utils import timezone
from decimal import Decimal
import yfinance as yf

# Create your models here.


class StockPortfolio(models.Model):
    """
    StockPortfolio is the main container for all StockAccounts. 
    """
    portfolio = models.OneToOneField(
        'portfolio.Portfolio', on_delete=models.CASCADE, related_name='stock_portfolio'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    custom_columns = models.JSONField(default=dict, blank=True)

    def get_default_columns(self):
        # Return a dict of default columns
        return {
            'stock': True,
            'shares': True,
            'purchase_price': True,
            'price': True,
            'total_investment': True,
            'dividends': True
        }

    def __str__(self):
        return f"{self.portfolio}"

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
    last_price = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)
    is_not_in_database = models.BooleanField(default=False)

    def __str__(self):
        return self.ticker

    def fetch_yfinance_data(self, force_update=False):
        """
        Fetch data from yfinance and update the model. If force_update=False, use cached data if recent.
        """
        # Check if data is recent (e.g., within 1 day) and not forced.
        if not force_update and self.last_updated and (timezone.now() - self.last_updated.days < 1):
            return {
                'price': self.last_price,
                'dividends': self.dividend_rate,
                'currency': self.currency,
                'stock_exchange': self.stock_exchange,
                'is_etf': self.is_etf,
            }

        ticker = yf.Ticker(self.ticker)
        try:
            info = ticker.info
            if not info or 'symbol' not in info or info['symbol'] != self.ticker.upper():
                self.is_not_in_database = True
                self.save(update_fields=['is_not_in_database'])
                return {}

            # Update fields based on yfinance data
            self.is_etf = info.get('quoteType') == 'ETF'
            self.currency = info.get('currency')
            self.stock_exchange = info.get('exchange')
            self.dividend_rate = Decimal(str(info.get('dividendRate', 0) or 0))
            self.last_price = Decimal(str(info.get('currentPrice') or info.get(
                'regularMarketPrice') or info.get('previousClose') or 0))
            self.last_updated = timezone.now()
            self.is_not_in_database = False

            # Save updated fields
            self.save(update_fields=['is_etf', 'currency', 'stock_exchange',
                      'dividend_rate', 'last_price', 'last_updated', 'is_not_in_database'])
            return {
                'price': self.last_price,
                'dividends': self.dividend_rate,
                'currency': self.currency,
                'stock_exchange': self.stock_exchange,
                'is_etf': self.is_etf,
            }
        except Exception as e:
            self.is_not_in_database = True
            self.save(update_fields=['is_not_in_database'])
            return {}


class SelfManagedAccount(models.Model):
    stock_portfolio = models.ForeignKey(
        StockPortfolio, on_delete=models.CASCADE, related_name='self_managed_accounts'
    )
    account_name = models.CharField(
        max_length=255, default='Self Managed Account')
    created_at = models.DateTimeField(auto_now_add=True)
    stocks = models.ManyToManyField(
        Stock, through='StockHolding', related_name='self_managed_accounts', blank=True
    )

    def __str__(self):
        return f"{self.account_name} - {self.stock_portfolio.name}"


class StockHolding(models.Model):
    stock_account = models.ForeignKey(
        SelfManagedAccount, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    shares = models.DecimalField(max_digits=15, decimal_places=4)
    purchase_price = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True)
    custom_data = models.JSONField(default=dict, blank=True)
    custom_ticker = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        unique_together = ('stock_account', 'stock', 'custom_ticker')

    def __str__(self):
        return f"{self.stock.ticker if self.stock else self.custom_ticker} ({self.shares} shares)"


class CustomStockHolding(models.Model):
    stock_account = models.ForeignKey(
        SelfManagedAccount, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=10)
    shares = models.DecimalField(max_digits=15, decimal_places=4)
    purchase_price = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True)
    custom_data = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ('stock_account', 'ticker')

    def __str__(self):
        return f"{self.ticker} ({self.shares} shares)"
