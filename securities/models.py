from django.db import models
from portfolio.models import IndividualPortfolio
from django.utils import timezone

# Create your models here.


class StockPortfolio(models.Model):
    individual_portfolio = models.OneToOneField(
        'portfolio.IndividualPortfolio', on_delete=models.CASCADE, related_name='stock_portfolio'
    )
    name = models.CharField(max_length=255, default="Stock Portfolio")
    created_at = models.DateTimeField(auto_now_add=True)
    custom_columns = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.name} - {self.individual_portfolio.name}"

    def get_default_columns(self):
        return {
            "ticker": None,
            "name": None,
            "price": None,
            "shares": None,
            "total_investment": None,
            "currency": None,
            "purchase_price": None,
            "dividends": None,
            "stock_tags": None
        }


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
    name = models.CharField(max_length=255, blank=True)
    currency = models.CharField(max_length=10, blank=True)
    # Fetched Data
    price = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True)  # Cached price
    dividends = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True)  # Cached dividends
    last_updated = models.DateTimeField(
        null=True, blank=True)  # When data was last fetched
    is_etf = models.BooleanField(default=False)

    def __str__(self):
        return self.ticker

    def update_from_yfinance(self):
        import yfinance as yf
        ticker = yf.Ticker(self.ticker)
        try:
            info = ticker.info
            # Determine if it's an ETF
            self.is_etf = info.get('quoteType') == 'ETF'

            # Price: Handle stocks vs ETFs
            if self.is_etf:
                self.price = info.get(
                    'regularMarketPrice') or info.get('previousClose')
            else:
                self.price = info.get('currentPrice') or info.get(
                    'regularMarketPrice') or info.get('previousClose')

            # Dividends: Handle stocks vs ETFs
            if self.is_etf:
                # ETFs often report yield or trailing annual dividend
                self.dividends = info.get(
                    'trailingAnnualDividendRate') or info.get('dividendRate')
            else:
                self.dividends = info.get('dividendRate')

            # Common fields
            self.name = info.get(
                'longName', info.get('shortName', self.ticker))
            self.currency = info.get('currency', 'USD')
            self.last_updated = timezone.now()
            self.save()
        except Exception as e:
            print(f"Failed to update {self.ticker}: {e}")
            if not self.name:
                self.name = self.ticker
            if not self.currency:
                self.currency = 'USD'
            self.last_updated = timezone.now()
            self.save()


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
