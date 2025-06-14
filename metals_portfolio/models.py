from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from portfolio.models import Asset, Portfolio, BaseAssetPortfolio, AssetHolding
from schemas.models import Schema, SchemaColumn, SchemaColumnValue
from .utils import get_precious_metal_price
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


# ------------------------------- SCHEMA ------------------------------ #

class MetalPortfolioSchema(Schema):
    pass


class MetalPortfolioSchemaColumn(SchemaColumn):
    pass


class MetalPortfolioSchemaColumnValue(SchemaColumnValue):
    pass


class PreciousMetal(Asset):
    """
    Represents a type of precious metal.
    """
    symbol = models.CharField(max_length=10, unqiue=True)
    name = models.CharField(max_length=50)
    price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
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

    def fetch_price(self, force_update=False):
        if self.is_custom:
            logger.info(f"Skipping fetch for custom metal {self.symbol}")
            return True

        if not force_update and self.last_updated and (timezone.now() - self.last_updated).seconds < 60 * 15:
            logger.debug(f"Using cached price for {self.symbol}")
            return True

        price = get_precious_metal_price(self.symbol)

        if price:
            self.price = Decimal(str(price))
            self.last_updated = timezone.now()
            self.save(updated_fields=["price", "last_updated"])
            logger.info(f"Updated price for {self.symbol}: {self.price}")
            return True

        logger.warning(f"Could not fetch price for {self.symbol}")
        return False

    @classmethod
    def create_from_symbol(cls, symbol: str, is_custom=False):
        symbol = symbol.upper()
        existing = cls.objects.filter(symbol=symbol).first()
        if existing:
            return existing

        instance = cls(symbol=symbol, name=symbol, is_custom=is_custom)

        if not is_custom:
            success = instance.fetch_price()
            if not success:
                instance.is_custom = True

        instance.save()
        return instance


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
            raise ValidationError(
                "Only one MetalsPortfolio is allowed per Portfolio.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super.save(*args, **kwargs)


class StorageFacility(models.Model):
    """
    Defines where the precious metals are stored.
    """
    name = models.CharField(max_length=100)
    metals_portfolio = models.ForeignKey(
        MetalsPortfolio,
        on_delete=models.CASCADE,
        related_name='storage_facilities'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_lending_account = models.BooleanField(default=False)
    is_insured = models.BooleanField(default=False)
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)

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
    metal = models.ForeignKey(
        PreciousMetal,
        on_delete=models.CASCADE,
        related_name='holdings'
    )
    weight_oz = models.DecimalField(max_digits=10, decimal_places=4)
    purchase_price_per_oz = models.DecimalField(
        max_digits=12, decimal_places=2)

    def get_current_value(self):
        return self.weight_oz * self.metal.get_current_value()

    def get_unrealized_gain(self):
        current_value = self.get_current_value()
        invested = self.weight_oz * self.purchase_price_per_oz
        return current_value - invested
