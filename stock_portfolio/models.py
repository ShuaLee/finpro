from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from portfolio.models import AssetHolding, StockPortfolio
from portfolio.utils import get_fx_rate
from schemas.models import StockPortfolioSchema, StockPortfolioSC, StockPortfolioSCV
from .constants import SCHEMA_COLUMN_CONFIG
from .utils import get_default_for_type
from decimal import Decimal, InvalidOperation
import logging


logger = logging.getLogger(__name__)


class BaseStockAccount(models.Model):
    """
    Abstract class for all stock account models.
    """
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    # Stock account specific fields
    broker = models.CharField(max_length=100, blank=True, null=True,
                              help_text="Brokerage platform (e.g. Robinhood, Interactive Brokers, etc.)")
    tax_status = models.CharField(
        max_length=50,
        choices=[('taxable', 'Taxable'),
                 ('tax_deferred', 'Tax-Deferred'),
                 ('tax_exempt', 'Tax-Exempt'),],
        default='taxable'
    )
    account_type = models.CharField(
        max_length=50,
        choices=[
            ('individual', 'Individual'),
            ('retirement', 'Retirement'),
            ('speculative', 'Speculative'),
            ('dividend', 'Dividend Focus'),
        ],
        default='individual',
        help_text="Purpose or strategy of the account."
    )
    last_synced = models.DateTimeField(
        null=True, blank=True, help_text="Last sync with broker.")

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class SelfManagedAccount(BaseStockAccount):
    stock_portfolio = models.ForeignKey(
        StockPortfolio,
        on_delete=models.CASCADE,
        related_name='self_managed_accounts'
    )
    active_schema = models.ForeignKey(
        StockPortfolioSchema,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Schema used to display stock holdings for this account."
    )

    def get_total_current_value_in_profile_fx(self):
        total = Decimal(0.0)
        for holding in self.holdings.all():
            value = holding.get_current_value_profile_fx()
            if value is not None:
                total += Decimal(str(value))
        return round(total, 2)

    def save(self, *args, **kwargs):
        if not self.pk and not self.active_schema:  # On creation, set active_schema
            if self.stock_portfolio and self.stock_portfolio.schemas.exists():
                self.active_schema = self.stock_portfolio.schemas.first()
            else:
                raise ValidationError(
                    "StockPortfolio must have at least one schema.")

        super().save(*args, **kwargs)


class ManagedAccount(BaseStockAccount):
    stock_portfolio = models.ForeignKey(
        StockPortfolio,
        on_delete=models.CASCADE,
        related_name='managed_accounts'
    )
    current_value = models.DecimalField(max_digits=12, decimal_places=2)
    invested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    strategy = models.CharField(max_length=100, null=True, blank=True)
    currency = models.CharField(
        max_length=3,
        choices=settings.CURRENCY_CHOICES,
        blank=True,
        null=True
    )

    class Meta:
        unique_together = (('stock_portfolio', 'name'),)

    def save(self, *args, **kwargs):
        if not self.currency and self.stock_portfolio and self.stock_portfolio.portfolio:
            self.currency = self.stock_portfolio.portfolio.profile.currency
        super().save(*args, **kwargs)

    def get_total_current_value_in_profile_fx(self):
        to_currency = self.stock_portfolio.portfolio.profile.currency
        fx = get_fx_rate(self.currency, to_currency)

        try:
            fx_decimal = Decimal(str(fx)) if fx is not None else Decimal(1)
        except:
            fx_decimal = Decimal(1)

        return round(self.current_value * fx_decimal, 2)

# -------------------- STOCK & STOCK HOLDING -------------------- #


class StockHolding(AssetHolding):
    self_managed_account = models.ForeignKey(
        SelfManagedAccount,
        on_delete=models.CASCADE,
        related_name='holdings',
    )
    stock = models.ForeignKey(
        'stocks.Stock',
        on_delete=models.CASCADE,
        related_name='holdings'
    )

    class Meta:
        indexes = [
            models.Index(fields=['self_managed_account']),
            models.Index(fields=['stock']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['self_managed_account', 'stock'],
                name='unique_holding_per_account'
            ),
        ]

    def __str__(self):
        return f"{self.stock} ({self.quantity} shares)"

    def get_column_value(self, source_field):
        # Try to find the existing value
        val = self.column_values.select_related('column').filter(
            column__source_field=source_field).first()

        if not val:
            schema = self.self_managed_account.active_schema
            config = SCHEMA_COLUMN_CONFIG.get('holding', {}).get(source_field)

            if config:
                # Try to find or create the missing column
                column, created = StockPortfolioSC.objects.get_or_create(
                    schema=schema,
                    source='holding',
                    source_field=source_field,
                    defaults={
                        'title': source_field.replace('_', ' ').title(),
                        'editable': config.get('editable', True)
                    }
                )

                # Only create the value if it doesn't already exist
                val, val_created = StockPortfolioSCV.objects.get_or_create(
                    column=column,
                    holding=self,
                    defaults={
                        'value': get_default_for_type(config.get('data_type')),
                        'is_edited': False
                    }
                )

        return val.get_value() if val else getattr(self, source_field, None)

    def get_current_value(self):
        # Use edited values if available via SchemaColumnValue
        quantity = self.get_column_value('quantity')
        price = self.get_column_value('price')

        try:
            if quantity is not None and price is not None:
                return round(float(quantity) * float(price), 2)
        except (TypeError, ValueError):
            pass
        return None

    def get_current_value_profile_fx(self):
        price = self.get_column_value('price')
        quantity = self.get_column_value('quantity')
        from_currency = self.stock.currency
        to_currency = self.self_managed_account.stock_portfolio.portfolio.profile.currency
        fx_rate = get_fx_rate(from_currency, to_currency)

        try:
            if quantity is not None and price is not None and fx_rate is not None:
                return round(float(quantity) * float(price) * float(fx_rate), 2)
        except (TypeError, ValueError):
            pass
        return None

    def get_unrealized_gain(self):
        try:
            quantity = self.get_column_value('quantity')
            price = self.get_column_value('price')
            purchase_price = self.get_column_value('purchase_price')

            if None in (quantity, price, purchase_price):
                return None

            quantity = Decimal(str(quantity))
            price = Decimal(str(price))
            purchase_price = Decimal(str(purchase_price))

            return round((price - purchase_price) * quantity, 2)
        except (InvalidOperation, TypeError, ValueError):
            return None

    def get_unrealized_gain_profile_fx(self):
        try:
            quantity = self.get_column_value('quantity')
            price = self.get_column_value('price')
            purchase_price = self.get_column_value('purchase_price')
            from_currency = self.stock.currency
            to_currency = self.self_managed_account.stock_portfolio.portfolio.profile.currency
            fx_rate = get_fx_rate(from_currency, to_currency)

            if None in (quantity, price, purchase_price, fx_rate):
                return None

            quantity = Decimal(str(quantity))
            price = Decimal(str(price))
            purchase_price = Decimal(str(purchase_price))
            fx_rate = Decimal(str(fx_rate))

            unrealized = (price - purchase_price) * quantity * fx_rate
            return round(unrealized, 2)
        except (InvalidOperation, TypeError, ValueError):
            return None

    def get_performance(self):
        current_value = self.get_current_value()
        invested = self.purchase_price or 0
        try:
            if current_value is None or invested in (None, 0):
                return None
            return ((Decimal(str(current_value)) - Decimal(str(invested))) / Decimal(str(invested))) * 100
        except (InvalidOperation, ZeroDivisionError):
            return None
