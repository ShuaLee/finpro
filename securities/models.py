from django.db import models
from portfolio.models import Portfolio
from django.utils import timezone
from decimal import Decimal
import yfinance as yf

# Create your models here.


class StockPortfolio(models.Model):
    portfolio = models.OneToOneField(
        'portfolio.Portfolio', on_delete=models.CASCADE, related_name='stock_portfolio'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.portfolio}"


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

    def __str__(self):
        return self.ticker

    def fetch_yfinance_data(self, fields):
        ticker = yf.Ticker(self.ticker)
        try:
            info = ticker.info
            # Determine if it's an ETF
            self.is_etf = info.get('quoteType') == 'ETF'
            result = {}

            # Map requested fields to yfinance keys, with ETF handling
            for field in fields:
                if field == 'price':
                    if self.is_etf:
                        value = info.get('regularMarketPrice') or info.get(
                            'previousClose')
                    else:
                        value = info.get('currentPrice') or info.get(
                            'regularMarketPrice') or info.get('previousClose')
                elif field == 'dividends':
                    if self.is_etf:
                        value = info.get('trailingAnnualDividendRate') or info.get(
                            'dividendRate')
                    else:
                        value = info.get('dividendRate')
                elif field == 'name':
                    value = info.get('longName', info.get(
                        'shortName', self.ticker))
                else:
                    # Generic fetch for other fields (e.g., marketCap)
                    value = info.get(field)

                # Convert to Decimal for monetary fields
                if value is not None and field in ['price', 'dividends', 'marketCap', 'regularMarketPrice', 'previousClose', 'trailingAnnualDividendRate']:
                    value = Decimal(str(value))
                result[field] = value

            # Update is_etf and save only if changed
            self.save(update_fields=['is_etf'] if self.pk else None)
            return result
        except Exception as e:
            print(f"Failed to fetch {self.ticker}: {e}")
            return {}


class StockAccount(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('self_managed', 'Self Managed'),
        ('managed', 'Managed'),
    ]

    stock_portfolio = models.ForeignKey(
        StockPortfolio, on_delete=models.CASCADE, related_name='stock_accounts'
    )
    account_type = models.CharField(
        max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='self_managed'
    )
    account_name = models.CharField(max_length=255, default='Stock Account')
    created_at = models.DateTimeField(auto_now_add=True)
    stocks = models.ManyToManyField(
        Stock, through='StockHolding', related_name='stock_accounts', blank=True)

    def __str__(self):
        return f"{self.account_name} - {self.stock_portfolio.name}"


class StockHolding(models.Model):
    stock_account = models.ForeignKey(StockAccount, on_delete=models.CASCADE)
    stock = models.ForeignKey('Stock', on_delete=models.CASCADE)
    shares = models.DecimalField(max_digits=15, decimal_places=4)
    purchase_price = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('stock_account', 'stock')

    def __str__(self):
        return f"{self.stock.ticker} ({self.shares} shares)"
