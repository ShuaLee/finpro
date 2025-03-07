from django.db import models
from portfolio.models import IndividualPortfolio
from core.models import Profile

# Create your models here.


class StockTag(models.Model):
    # e.g. "Coal Producer", "Tech", etc.
    name = models.CharField(max_length=100)
    """
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='stock_tags'
    )
    """
    stock_account = models.ForeignKey(
        'StockAccount', on_delete=models.CASCADE, related_name='stock_tags'
    )

    # Nested sub-tags
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE, related_name='sub_tags'
    )

    def __str__(self):
        return self.name


class StockAccount(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('self_managed', 'Self Managed'),
        ('managed', 'Managed'),
    ]

    portfolio = models.ForeignKey(
        IndividualPortfolio, on_delete=models.CASCADE, related_name='stock_account'
    )
    account_type = models.CharField(
        max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='self_managed'
    )
    account_name = models.CharField(max_length=255, default='Stock Account')
    created_at = models.DateTimeField(auto_now_add=True)
    stocks = models.ManyToManyField(
        'Stock', related_name='stock_accounts', blank=True)

    def __str__(self):
        return f"{self.account_name} - {self.portfolio.name}"

    class Meta:
        verbose_name = "Stock Account"
        verbose_name_plural = "Stock Accounts"


class Stock(models.Model):
    STOCK_TYPE_CHOICES = [
        ('stock', 'Stock'),
        ('etf', 'ETF'),
    ]

    ticker = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255)
    exchange = models.CharField(max_length=100)
    current_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10)
    dividends = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    sector = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    stock_type = models.CharField(
        max_length=20, choices=STOCK_TYPE_CHOICES, default='stock')
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.ticker} - {self.name} ({self.stock_type})"
