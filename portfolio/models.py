from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from core.models import Profile
import logging

logger = logging.getLogger(__name__)


class Portfolio(models.Model):
    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name='portfolio'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.profile} - {self.created_at}"


class InvestmentTheme(models.Model):
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name='asset_tags')
    name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtags')

    class Meta:
        unique_together = ('portfolio', 'name')

    def __str__(self):
        full_path = [self.name]
        parent = self.parent
        while parent is not None:
            full_path.append(parent.name)
            parent = parent.parent
        return " > ".join(reversed(full_path))


class BaseAssetPortfolio(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Asset(models.Model):
    class Meta:
        abstract = True

    def get_type(self):
        return self.__class__.__name__

    def get_current_value(self):
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
        if total_cost > 0:
            return (self.get_current_value() - total_cost) / total_cost * 100
        return 0

    def clean(self):
        if self.quantity < 0:
            raise ValidationError("Quantity cannot be negative.")
        if self.purchase_price and self.purchase_price < 0:
            raise ValidationError("Purchase price cannot be negative.")

    def save(self, *args, **kwargs):
        self.full_clean()
        logger.debug(
            f"Saving {self.__class__.__name__} for asset {getattr(self, 'asset', None)}")
        super().save(*args, **kwargs)
        return self


class FXRate(models.Model):
    from_currency = models.CharField(max_length=3)
    to_currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=20, decimal_places=6)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('from_currency', 'to_currency')]

    def __str__(self):
        return f"{self.from_currency} → {self.to_currency}: {self.rate}"

    def is_stale(self):
        return self.updated_at < timezone.now() - timedelta(hours=24)
