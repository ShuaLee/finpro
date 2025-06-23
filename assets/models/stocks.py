from django.db import models
from .base import Asset, AssetHolding
from accounts.models.stocks import SelfManagedAccount
from schemas.models.stocks import StockPortfolioSC, StockPortfolioSCV


class Stock(Asset):
    ticker = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    exchange = models.CharField(
        max_length=50, null=True, blank=True, help_text="Stock exchange (e.g., NYSE, NASDAQ)")
    is_adr = models.BooleanField(default=False)
    price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    currency = models.CharField(max_length=3, blank=True, null=True)
    average_volume = models.BigIntegerField(null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    dividend_yield = models.DecimalField(
        max_digits=6, decimal_places=4, blank=True, null=True)
    pe_ratio = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    quote_type = models.CharField(max_length=50, blank=True, null=True)
    sector = models.CharField(max_length=100, null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)

    is_custom = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['ticker']),
            models.Index(fields=['is_custom']),
            models.Index(fields=['exchange'])
        ]

    def __str__(self):
        return self.ticker

    def save(self, *args, **kwargs):
        if self.ticker:
            self.ticker = self.ticker.upper()
        super().save(*args, **kwargs)

    def get_price(self):
        return self.price or 0


class StockHolding(AssetHolding):
    self_managed_account = models.ForeignKey(
        SelfManagedAccount,
        on_delete=models.CASCADE,
        related_name='stock_holdings'
    )
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='stock_holdings'
    )

    @property
    def asset(self):
        return self.stock

    class Meta:
        indexes = [
            models.Index(fields=['self_managed_account']),
            models.Index(fields=['stock'])
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['self_managed_account', 'stock'],
                name='unique_holding_per_account'
            ),
        ]

    def __str__(self):
        return f"{self.stock} ({self.quantity} shares)"

    def get_profile_currency(self):
        return self.self_managed_account.stock_portfolio.portfolio.profile.currency

    # Methods for calculated ASSET_SCHEMA_CONFIG
    def get_column_value(self, source_field):
        return super().get_column_value(
            source_field,
            asset_type='stock',
            get_schema=lambda: self.self_managed_account.active_schema,
            column_model=StockPortfolioSC,
            column_value_model=StockPortfolioSCV,
        )
