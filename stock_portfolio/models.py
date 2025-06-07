from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models
from portfolio.models import Portfolio, BaseAssetPortfolio, AssetHolding
from schemas.models import Schema, SchemaColumn, SchemaColumnValue
from core.constants import CURRENCY_CHOICES
from .constants import SCHEMA_COLUMN_CONFIG
import logging
import numexpr

logger = logging.getLogger(__name__)


# ---------------------------- Schema ------------------------------ #

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
            raise PermissionDenied(
                "Cannot delete the last schema for a StockPortfolio.")
        super().delete(*args, **kwargs)


class StockPortfolioSchemaColumn(SchemaColumn):
    @staticmethod
    def get_source_field_choices():
        choices = []
        for source, fields in SCHEMA_COLUMN_CONFIG.items():
            for source_field in fields.keys():
                if source_field is not None:
                    label = source_field.replace('_', ' ').title()
                    choices.append((source_field, label))
        return choices

    SOURCE_FIELD_CHOICES = get_source_field_choices()

    schema = models.ForeignKey(
        StockPortfolioSchema,
        on_delete=models.CASCADE,
        related_name='columns'
    )
    source_field = models.CharField(
        max_length=100, choices=SOURCE_FIELD_CHOICES, blank=True)

    class Meta:
        unique_together = (('schema', 'title'),)

    def __str__(self):
        return f"[{self.schema.stock_portfolio.portfolio.profile}] {self.title} ({self.source})"

    def clean(self):
        if self.source in ['asset', 'holding'] and not self.source_field:
            raise ValidationError(
                "source_field is required for asset or holding sources.")
        if self.source == 'calculated' and not self.formula:
            raise ValidationError(
                "formula is required for calculated sources.")
        if self.source == 'custom' and (self.source_field or self.formula):
            raise ValidationError(
                "custom sources should not have source_field or formula.")
        # Validate source_field matches source
        if self.source == 'asset' and self.source_field not in ['ticker', 'price', 'name']:
            raise ValidationError("Invalid source_field for asset source.")
        if self.source == 'holding' and self.source_field not in ['quantity', 'purchase_price', 'holding.ticker']:
            raise ValidationError("Invalid source_field for holding source.")
        if self.source == 'calculated' and self.source_field not in ['current_value']:
            raise ValidationError(
                "Invalid source_field for calculated source.")

    def delete(self, *args, **kwargs):
        if not self.is_deletable:
            raise PermissionDenied(
                "This column is mandatory and cannot be deleted.")
        super().delete(*args, **kwargs)


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

    def clean(self):
        if self.column and self.holding:
            if self.holding.self_managed_account.stock_portfolio != self.column.schema.stock_portfolio:
                raise ValidationError(
                    "StockHolding and StockPortfolioSchemaColumn must belong to the same StockPortfolio."
                )
            # Enforce non-editable columns
            if not self.column.editable and (self.is_edited or self.value):
                raise ValidationError(
                    f"Cannot edit value for non-editable column '{self.column.title}'."
                )
            # Validate value type for holding source
            if self.column.source == 'holding' and self.value:
                if self.column.source_field == 'quantity':
                    try:
                        float(self.value)
                    except ValueError:
                        raise ValidationError(
                            "Quantity must be a valid number.")
                elif self.column.source_field == 'purchase_price':
                    try:
                        float(self.value)
                    except ValueError:
                        raise ValidationError(
                            "Purchase Price must be a valid number.")
                elif self.column.source_field == 'holding.ticker':
                    if not isinstance(self.value, str):
                        raise ValidationError("Ticker must be a string.")

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.column.source == 'holding' and self.value:
            if self.column.source_field == 'quantity':
                self.holding.quantity = float(self.value)
            elif self.column.source_field == 'purchase_price':
                self.holding.purchase_price = float(self.value)
            elif self.column.source_field == 'holding.ticker':
                self.holding.stock.ticker = self.value
            self.holding.save()
            self.value = None
            self.is_edited = False
        super().save(*args, **kwargs)

    def get_value(self):
        column = self.column
        config = SCHEMA_COLUMN_CONFIG.get(
            column.source, {}).get(column.source_field)

        # Use edited value if present
        if self.is_edited and self.value is not None:
            raw = self.value
        else:
            # Derive the value from source
            if column.source == 'holding':
                if column.source_field == 'quantity':
                    raw = self.holding.quantity
                elif column.source_field == 'purchase_price':
                    raw = self.holding.purchase_price
                elif column.source_field == 'holding.ticker':
                    raw = self.holding.stock.ticker
                else:
                    raw = None
            elif column.source == 'asset' and self.holding.stock:
                raw = getattr(self.holding.stock, column.source_field, None)
            elif column.source == 'calculated':
                return self.evaluate_formula(column.formula)
            else:
                raw = self.value

        # Apply type casting
        if config:
            dtype = config.get("data_type")
            try:
                if dtype == "decimal":
                    val = float(raw)
                    # Limit to 2 decimal places if field is 'price'
                    if column.source_field == 'price':
                        return round(val, 2)
                    return val
                elif dtype == "string":
                    return str(raw)
            except (TypeError, ValueError):
                return None

        return raw

    def evaluate_formula(self, formula):
        if not formula:
            return None
        try:
            # Build context with quantity and price
            context = {
                'quantity': float(self.holding.quantity or 0),
                'price': float(getattr(self.holding.stock, 'price') or 0),
            }
            # Evaluate using numexpr
            result = numexpr.evaluate(formula, local_dict=context)
            # Convert to float for decimal compatibility
            return round(float(result), 2)
            # return f"{float(result):.2f}"  # Always 2 decimal places as string
        except Exception as e:
            logger.error(f"Failed to evaluate formula '{formula}': {str(e)}")
            return None

# ------------------------------------------------------------------ #

# -------------------- STOCK PORTFOLIO -------------------- #


class StockPortfolio(BaseAssetPortfolio):
    portfolio = models.OneToOneField(
        Portfolio,
        on_delete=models.CASCADE,
        related_name='stockportfolio'
    )

    def __str__(self):
        return f"Stock Portfolio for {self.portfolio.profile.user.email}"

    def clean(self):
        if self.pk is None and StockPortfolio.objects.filter(portfolio=self.portfolio).exists():
            raise ValidationError(
                "Only one StockPortfolio is allowed per Portfolio.")

        if self.pk and not self.schemas.exists():  # Only check schemas if saved
            raise ValidationError(
                "StockPortfolio must have at least one schema.")

    def save(self, *args, **kwargs):
        self.full_clean()  # Run clean before saving
        super().save(*args, **kwargs)


# -------------------- STOCK ACCOUNTS -------------------- #


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
