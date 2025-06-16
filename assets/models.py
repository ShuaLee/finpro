from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from decimal import Decimal
from portfolio.models import InvestmentTheme
from stock_portfolio.models import SelfManagedAccount
import logging

logger = logging.getLogger(__name__)

# ------------------------------ ABSTRACT CLASSES ----------------------------- #


class Asset(models.Model):
    class Meta:
        abstract = True

    def get_type(self):
        return self.__class__.__name__

    def get_price(self):
        raise NotImplementedError


class AssetHolding(models.Model):
    quantity = models.DecimalField(max_digits=15, decimal_places=4)
    purchase_price = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True)
    purchase_date = models.DateTimeField(null=True, blank=True)
    investment_theme = models.ForeignKey(
        InvestmentTheme,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='holdings'
    )

    class Meta:
        abstract = True

    def get_current_value(self):
        if hasattr(self, 'asset') and self.quantity:
            return self.quantity * self.asset.get_current_value()
        return 0

    def get_total_cost(self):
        if self.quantity and self.purchase_price:
            return self.quantity * self.purchase_price
        return 0

    def get_performance(self):
        total_cost = self.get_total_cost()
        current_value = Decimal(str(self.get_current_value()))  # cast safely
        if total_cost > 0:
            return (current_value - total_cost) / total_cost * 100
        return 0

    def clean(self):
        if self.quantity < 0:
            raise ValidationError("Quantity cannot be negative.")
        if self.purchase_price and self.purchase_price < 0:
            raise ValidationError("Purchase price cannot be negative.")
        if self.purchase_date and self.purchase_date > timezone.now():
            raise ValidationError("Purchase date cannot be in the future.")

    def save(self, *args, **kwargs):
        self.full_clean()
        logger.debug(
            f"Saving {self.__class__.__name__} for asset {getattr(self, 'asset', None)}")
        super().save(*args, **kwargs)
        return self

# ------------------------------ STOCKS ------------------------------- #


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