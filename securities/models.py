from django.db import models
from portfolio.models import Portfolio
from django.utils import timezone
from decimal import Decimal
import yfinance as yf
import logging

logger = logging.getLogger(__name__)

# Create your models here.


class StockPortfolio(models.Model):
    """
    StockPortfolio is the main container for all StockAccounts. 
    """
    portfolio = models.OneToOneField(
        'portfolio.Portfolio', on_delete=models.CASCADE, related_name='stock_portfolio'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    holding_display = models.JSONField(default=dict, blank=True)

    def get_default_holding_display_config(self):
        return {
            'ticker': {'visible': True, 'editable': False, 'auto': True, 'edited': False},
            'shares': {'visible': True, 'editable': True, 'auto': True, 'edited': False},
            'purchase_price': {'visible': True, 'editable': True, 'auto': True, 'edited': False},
            'price': {'visible': True, 'editable': True, 'auto': True, 'edited': False},
            'total_investment': {'visible': True, 'editable': True, 'auto': True, 'edited': False},
            'dividends': {'visible': True, 'editable': True, 'auto': True, 'edited': False},
        }

    def save(self, *args, **kwargs):
        if not self.holding_display:
            self.holding_display = self.get_default_holding_display_config()
        super().save(*args, **kwargs)
        if 'update_fields' not in kwargs or 'holding_display' in kwargs.get('update_fields', []):
            for account in self.self_managed_accounts.all():
                for holding in account.stockholding_set.all():
                    holding.sync_holding_display(save=False)

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
        SelfManagedAccount, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, null=True, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=10)
    shares = models.DecimalField(max_digits=15, decimal_places=4)
    purchase_price = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True)
    holding_display = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ('stock_account', 'ticker')

    def __str__(self):
        return f"{self.ticker} ({self.shares} shares)"

    def sync_holding_display(self, save=True):
        portfolio = self.stock_account.stock_portfolio
        template = portfolio.holding_display
        updated_display = {}

        for column_name, config in template.items():
            # Copy the full config, including 'edited': False
            updated_display[column_name] = config.copy()

            if column_name == 'ticker':
                updated_display[column_name]['value'] = self.ticker
                # ticker is not editable, so 'edited' stays False
            elif column_name == 'shares':
                updated_display[column_name]['value'] = str(self.shares)
                existing = self.holding_display.get(
                    column_name, {}).get('value')
                if existing and existing != str(self.shares):
                    updated_display[column_name]['edited'] = True
            elif column_name == 'purchase_price':
                updated_display[column_name]['value'] = str(
                    self.purchase_price) if self.purchase_price else None
                existing = self.holding_display.get(
                    column_name, {}).get('value')
                if existing and existing != (str(self.purchase_price) if self.purchase_price else None):
                    updated_display[column_name]['edited'] = True
            elif column_name == 'price':
                default_value = str(
                    self.stock.last_price) if self.stock and self.stock.last_price else None
                existing = self.holding_display.get(
                    column_name, {}).get('value')
                if existing and existing != default_value:
                    updated_display[column_name]['value'] = existing
                    updated_display[column_name]['edited'] = True
                else:
                    updated_display[column_name]['value'] = default_value
                    # Explicitly reset to False if matching default
                    updated_display[column_name]['edited'] = False
            elif column_name == 'total_investment':
                default_price = Decimal(self.holding_display.get(
                    'price', {}).get('value', '0') or '0')
                default_value = str(
                    default_price * self.shares) if default_price else None
                existing = self.holding_display.get(
                    column_name, {}).get('value')
                if existing and existing != default_value:
                    updated_display[column_name]['value'] = existing
                    updated_display[column_name]['edited'] = True
                else:
                    updated_display[column_name]['value'] = default_value
                    # Explicitly reset to False if matching default
                    updated_display[column_name]['edited'] = False
            elif column_name == 'dividends':
                if self.stock:
                    if self.stock.is_etf:
                        yield_percent = self.stock.dividend_yield or Decimal(
                            '0')
                        total_investment = Decimal(updated_display.get(
                            'total_investment', {}).get('value', '0') or '0')
                        default_value = str(
                            (total_investment * yield_percent) / Decimal('100')) if yield_percent else None
                    else:
                        rate = self.stock.dividend_rate or Decimal('0')
                        default_value = str(
                            rate * self.shares) if rate else None
                else:
                    default_value = None
                existing = self.holding_display.get(
                    column_name, {}).get('value')
                if existing and existing != default_value:
                    updated_display[column_name]['value'] = existing
                    updated_display[column_name]['edited'] = True
                else:
                    updated_display[column_name]['value'] = default_value
                    # Explicitly reset to False if matching default
                    updated_display[column_name]['edited'] = False

        self.holding_display = updated_display
        if save:
            super().save(update_fields=['holding_display'])

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.sync_holding_display(save=False)
