from django.db import models
from portfolio.models import IndividualPortfolio
from core.models import Profile

# Create your models here.


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

    def __str__(self):
        return self.ticker


class StockAccount(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('self_managed', 'Self Managed'),
        ('managed', 'Managed'),
    ]

    portfolio = models.ForeignKey(
        IndividualPortfolio, on_delete=models.CASCADE, related_name='stock_accounts'
    )
    account_type = models.CharField(
        max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='self_managed'
    )
    account_name = models.CharField(max_length=255, default='Stock Account')
    created_at = models.DateTimeField(auto_now_add=True)
    stocks = models.ManyToManyField(
        Stock, through='StockHolding', related_name='stock_accounts', blank=True)

    # Custom columns as a list (e.g., ['ticker', 'name', 'price', ...])
    custom_columns = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.account_name} - {self.portfolio.name}"

    def get_default_columns(self):
        return [
            "ticker", "name", "price", "shares", "total_investment",
            "currency", "purchase_price", "dividends", "stock_tags"
        ]

    class Meta:
        verbose_name = "Stock Account"
        verbose_name_plural = "Stock Accounts"


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
