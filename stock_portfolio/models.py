from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models
from portfolio.models import BaseAssetPortfolio, AssetHolding, BaseInvestmentAccount
from schemas.models import Schema, SchemaColumn, SchemaColumnValue
from .constants import STOCK_FIELDS, CALCULATION_FORMULAS, FIELD_DATA_TYPES
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
    
    def delete(self, *args, **kwargs):
        if self.stock_portfolio.schemas.count() <= 1:
            raise PermissionDenied("Cannot delete the last schema for a StockPortfolio.")
        super().delete(*args, **kwargs)


class StockPortfolioSchemaColumn(SchemaColumn):
    schema = models.ForeignKey(
        StockPortfolioSchema,
        on_delete=models.CASCADE,
        related_name='columns'
    )

    class Meta:
        unique_together = (('schema', 'name'), ('schema', 'source_field'))

    def save(self, *args, **kwargs):
        # Ensure source_field and data_type align with constants
        if self.source in ['asset', 'holding', 'calculated']:
            valid_fields = {f[0] for f in STOCK_FIELDS if f[2] == self.source}
            if self.source_field not in valid_fields:
                raise ValidationError(
                    f"Invalid source_field '{self.source_field}' for source '{self.source}'.")
            expected_data_type = FIELD_DATA_TYPES.get(self.source_field)
            if self.data_type != expected_data_type:
                logger.warning(
                    f"Data type mismatch for {self.source_field}: expected {expected_data_type}, got {self.data_type}"
                )
                self.data_type = expected_data_type
        if self.source == 'calculated':
            self.formula = CALCULATION_FORMULAS.get(self.source_field, '')
        super().save(*args, **kwargs)


class StockPortfolioSchemaColumnValue(SchemaColumnValue):
    column = models.ForeignKey(
        StockPortfolioSchemaColumn,
        on_delete=models.CASCADE,
        related_name='values'
    )
    holding = models.ForeignKey(
        'StockHolding',
        on_delete=models.CASCADE,
        related_name='column_values'
    )

    class Meta:
        unique_together = (('column', 'holding'),)

    def get_value(self):
        """Return the user-edited value or the derived value."""
        if self.is_edited and self.value is not None:
            return self.value
        column = self.column
        if column.source == 'asset' and self.holding.asset:
            # Fetch from asset (Stock or CustomStock)
            return getattr(self.holding.asset, column.source_field, None)
        elif column.source == 'holding':
            # Fetch from holding
            return getattr(self.holding, column.source_field, None)
        elif column.source == 'calculated':
            # Evaluate formula
            return self.evaluate_formula(column.formula)
        return self.value

    def evaluate_formula(self, formula):
        """Evaluate the formula using holding and asset fields."""
        if not formula:
            return None
        try:
            # Replace field names with actual values
            context = {}
            for field, _, source, source_field in STOCK_FIELDS:
                if source == 'asset' and self.holding.asset:
                    context[field] = getattr(
                        self.holding.asset, source_field, 0)
                elif source == 'holding':
                    context[field] = getattr(self.holding, source_field, 0)
                else:
                    context[field] = 0
            # Safe evaluation (simplified; use a proper parser like numexpr in production)
            formula = formula.replace(' * ', '*').replace(' / ', '/')
            for field in context:
                formula = formula.replace(field, str(context[field] or 0))
            # WARNING: Use a safe evaluator in production
            return eval(formula, {"__builtins__": {}}, {})
        except Exception as e:
            logger.error(f"Failed to evaluate formula '{formula}': {str(e)}")
            return None

# -------------------- STOCK PORTFOLIO -------------------- #


class StockPortfolio(BaseAssetPortfolio):
    def __str__(self):
        return f"Stock Portfolio for {self.portfolio.profile.user.email}"
    
    def clean(self):
        if not self.schemas.exists():
            raise ValidationError("StockPortfolio must have at least one schema.")
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Run clean before saving
        super().save(*args, **kwargs)
        

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
