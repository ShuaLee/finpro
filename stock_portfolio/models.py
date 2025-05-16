from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from portfolio.models import BaseAssetPortfolio, AssetHolding, BaseInvestmentAccount
from schemas.models import Schema, SchemaColumn, SchemaColumnValue
from stocks.models import Stock, CustomStock
from .constants import CURRENCY_CHOICES
import logging

logger = logging.getLogger(__name__)


# ------------------ Schema -------------------- #
class StockPortfolioSchema(Schema):
    stock_portfolio = models.ForeignKey(
        'stock_portfolio.StockPortfolio',
        on_delete=models.CASCADE,
        related_name='schemas'
    )

    class Meta:
        unique_together = (('stock_portfolio', 'name'))


class StockPortfolioSchemaColumn(SchemaColumn):
    schema = models.ForeignKey(
        'stock_portfolio.StockPortfolioSchema',
        on_delete=models.CASCADE,
        related_name='columns'
    )

    class Meta:
        unique_together = (('schema', 'name'))


class StockPortfolioSchemaColumnValue(SchemaColumnValue):
    pass

# -------------------- Cash Balances -------------------- #


class CashBalance(models.Model):
    account = models.ForeignKey(
        'SelfManagedAccount', on_delete=models.CASCADE, related_name='cash_balances')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('account', 'currency')

    def __str__(self):
        return f"{self.amount} {self.currency}"

# -------------------- STOCK PORTFOLIO -------------------- #


class StockPortfolio(BaseAssetPortfolio):
    default_self_managed_schema = models.ForeignKey(
        StockPortfolioSchema,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_for_self_managed_accounts',
    )
    default_managed_schema = models.ForeignKey(
        StockPortfolioSchema,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_for_managed_accounts',
    )

    def __str__(self):
        return f"Stock Portfolio for {self.portfolio.profile.user.email}"

    def clean(self):
        if self.default_self_managed_schema and self.default_self_managed_schema.stock_portfolio != self:
            raise ValidationError(
                "Default schema must belong to this portfolio.")

    def save(self, *args, **kwargs):
        if not self._state.adding and self.default_self_managed_schema is None:
            raise ValueError("default_schema must not be null after creation.")

        if self.pk:
            old = StockPortfolio.objects.get(pk=self.pk)
            old_default = old.default_self_managed_schema
        else:
            old_default = None

        super().save(*args, **kwargs)

        # Now update only accounts still using the old default
        if self.default_self_managed_schema and old_default and self.default_self_managed_schema != old_default:
            self.self_managed_accounts.filter(
                active_schema=old_default
            ).update(active_schema=self.default_self_managed_schema)

# -------------------- STOCK ACCOUNTS -------------------- #


class BaseStockAccount(BaseInvestmentAccount):
    """
    Abstract class for all stock account models.
    """
    stock_portfolio = models.ForeignKey(
        StockPortfolio,
        on_delete=models.CASCADE,
        related_name='%(class)s_set'
    )
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
    use_default_schema = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Set default currency
        if not self.pk and not self.currency:
            try:
                profile = self.stock_portfolio.portfolio.profile
                self.currency = profile.currency or 'USD'
            except AttributeError:
                self.currency = 'USD'  # Fallback

        super().save(*args, **kwargs)


class SelfManagedAccount(BaseStockAccount):
    active_schema = models.ForeignKey(
        StockPortfolioSchema,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Schema used to display stock holdings for this account."
    )

    def save(self, *args, **kwargs):
        if self.use_default_schema:
            self.active_schema = self.stock_portfolio.default_self_managed_schema

        if self.active_schema and self.active_schema.stock_portfolio != self.stock_portfolio:
            raise ValidationError(
                "Selected schema does not belong to this account's stock portfolio.")

        super().save(*args, **kwargs)


class ManagedAccount(BaseStockAccount):
    current_value = models.DecimalField(max_digits=12, decimal_places=2)
    invested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    strategy = models.CharField(max_length=100, null=True, blank=True)

# -------------------- STOCK & STOCK HOLDING -------------------- #


class StockHolding(AssetHolding):
    def __str__(self):
        return f"{self.asset} ({self.quantity} shares)"

    def clean(self):
        super().clean()  # Call parent clean method for quantity and purchase_price validation
        # Restrict asset_content_type to Stock or CustomStock, if set
        if self.asset_content_type_id:  # Check the raw ID field instead of the descriptor
            valid_content_types = ContentType.objects.get_for_models(
                Stock, CustomStock).values()
            asset_content_type = ContentType.objects.get(
                id=self.asset_content_type_id)
            if asset_content_type not in valid_content_types:
                raise ValidationError(
                    f"Asset must be a Stock or CustomStock, not {asset_content_type}."
                )
