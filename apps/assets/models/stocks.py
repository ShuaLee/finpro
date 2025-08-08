from django.core.exceptions import ValidationError
from django.db import models
from .base import Asset, AssetHolding
from schemas.models import SchemaColumn, SchemaColumnValue


class Stock(Asset):
    ticker = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    exchange = models.CharField(max_length=50, null=True, blank=True, help_text="Stock exchange (e.g., NYSE, NASDAQ)")
    is_adr = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    currency = models.CharField(max_length=3, blank=True, null=True)
    average_volume = models.BigIntegerField(null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    dividend_yield = models.DecimalField(max_digits=6, decimal_places=4, blank=True, null=True)
    pe_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    is_etf = models.BooleanField(default=False)
    sector = models.CharField(max_length=100, null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)

    is_custom = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['ticker']),
            models.Index(fields=['is_custom']),
            models.Index(fields=['exchange']),
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
    account = models.ForeignKey(
        "accounts.StockAccount",
        on_delete=models.CASCADE,
        related_name='holdings'
    )
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='stock_holdings'
    )

    @property
    def asset(self):
        return self.stock

    def __str__(self):
        return f"{self.stock} ({self.quantity} shares)"

    def get_asset_type(self):
        return 'stock'

    def get_active_schema(self):
        # 🔧 use the unified account
        return self.account.active_schema

    def get_column_model(self):
        return SchemaColumn

    def get_column_value_model(self):
        return SchemaColumnValue

    def get_profile_currency(self):
        return self.account.stock_portfolio.portfolio.profile.currency

    class Meta:
        indexes = [
            models.Index(fields=['account']),
            models.Index(fields=['stock']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['account', 'stock'],
                name='unique_holding_per_account'
            ),
        ]

    def clean(self):
        # Only self-managed accounts can have holdings
        if self.account and self.account.account_mode != "self_managed":
            raise ValidationError("Holdings can only be added to self-managed accounts.")
        # keep base validations (quantity, purchase_price, purchase_date)
        super().clean()
