from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
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


class BaseAssetPortfolio(models.Model):
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="sub_portfolios")
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
    # Generic foreign key to BaseAssetPortfolio (e.g., StockPortfolio, CryptoPortfolio, etc.)
    portfolio_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='portfolio_holdings'
    )
    portfolio_object_id = models.PositiveIntegerField()
    base_asset_portfolio = GenericForeignKey('portfolio_content_type', 'portfolio_object_id')

    # Generic foreign key to Asset (e.g., Stock, Bitcoin, etc.)
    asset_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='asset_holdings'
    )
    asset_object_id = models.PositiveIntegerField()
    asset = GenericForeignKey('asset_content_type', 'asset_object_id')

    # Generic foreign ket to Account (e.g., SelfManagedAccount, CryptoWallet, etc.) nullable
    account_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='account_holdings'
    )
    account_object_id = models.PositiveIntegerField()
    account = GenericForeignKey('account_content_type', 'account_object_id')

    # Characteristics
    quantity = models.DecimalField(max_digits=15, decimal_places=4)
    purchase_price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    purchase_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'portfolio_content_type', 
                    'portfolio_object_id', 
                    'asset_content_type', 
                    'asset_object_id', 
                    'account_content_type', 
                    'account_object_id'
                    ],
                name='unique_holding'
            )
        ]

    def get_current_value(self):
        if self.asset and self.quantity:
            return self.quantity * self.asset.get_current_value() # This is calling the ASSETS get_current_value() not the holding
        return 0
    
    def get_total_cost(self):
        if self.quantity and self.purchase_price:
            return self.quantity * self.purchase_price
        return 0
    
    def get_performace(self):
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
        logger.debug(f"Saving {self.__class__.__name__} for asset {self.asset}, quantity={self.quantity}")
        super().save(*args, **kwargs)
        return self

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
