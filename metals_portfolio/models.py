from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from portfolio.models import Asset, Portfolio, BaseAssetPortfolio, AssetHolding
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class PreciousMetal(Asset):
    """
    Represents a type of precious metal.
    """
    symbol = models.CharField(max_length=10, unqiue=True)
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    currency = models.CharField(
        max_length=3, 
        choices=settings.CURRENCY_CHOICES,
        blank=True,
        null=True
    )
    is_custom = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name
    
    def get_current_value(self):
        return self.price or Decimal(0)
    
    """
    I need to implement the rest from ChatGPT
    """


class MetalsPortfolio(BaseAssetPortfolio):
    portfolio = models.OneToOneField(
        Portfolio,
        on_delete=models.CASCADE,
        related_name='metalsportfolio'
    )

    def __str__(self):
        return f"Precious Metals Portfolio for {self.portfolio.profile.user.email}"
    
    def clean(self):
        if self.pk is None and MetalsPortfolio.objects.filter(portfolio=self.portfolio).exists():
            raise ValidationError("Only one MetalsPortfolio is allowed per Portfolio.")
        
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super.save(*args, **kwargs)

class StorageFacility(models.Model):
    """
    Defines where the precious metals are stored.
    """
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    is_lending_account = models.BooleanField(default=False)
    is_insured = models.BooleanField(default=False)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)


    class Meta:
        abstract = True

    def __str__(self):
        return self.name
    
class PreciousMetalHolding(AssetHolding):
    storage_facility = models.ForeignKey(
        StorageFacility,
        on_delete=models.CASCADE,
        related_name='holdings'
    )