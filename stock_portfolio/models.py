from django.conf import settings
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models
from portfolio.models import Portfolio, BaseAssetPortfolio, AssetHolding
from portfolio.utils import get_fx_rate
from schemas.models import Schema, SchemaColumn, SchemaColumnValue
from .constants import SCHEMA_COLUMN_CONFIG
from .utils import resolve_field_path, get_default_for_type
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

    def save(self, *args, **kwargs):
        config = SCHEMA_COLUMN_CONFIG.get(self.source, {}).get(self.source_field)

        # Auto-correct source config fields if config found
        if config:
            self.data_type = config.get('data_type')
            self.editable = config.get('editable', True)
            if self.source == 'calculated':
                self.formula = config.get('formula', '')
            # Auto-correct title to be human-friendly from source_field
            if not self.title or self.title.strip().lower() == self.source_field.replace('_', ' ').lower():
                self.title = self.source_field.replace('_', ' ').title()

        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            holdings = StockHolding.objects.filter(
                self_managed_account__stock_portfolio=self.schema.stock_portfolio
            )
            for holding in holdings:
                StockPortfolioSchemaColumnValue.objects.get_or_create(
                    column=self,
                    holding=holding
                )

        # Ensure dependencies for calculated fields
        if self.source == 'calculated':
            dependency_fields = SCHEMA_COLUMN_CONFIG.get('calculated', {}).get(
                self.source_field, {}).get('context_fields', [])

            for field in dependency_fields:
                found = self.schema.columns.filter(source_field=field).exists()
                if not found:
                    for source_key, fields in SCHEMA_COLUMN_CONFIG.items():
                        if field in fields:
                            dep_config = fields[field]
                            StockPortfolioSchemaColumn.objects.get_or_create(
                                schema=self.schema,
                                source=source_key,
                                source_field=field,
                                defaults={
                                    'title': field.replace('_', ' ').title(),
                                    'data_type': dep_config['data_type'],
                                    'editable': dep_config.get('editable', True),
                                    'formula': dep_config.get('formula', ''),
                                    'is_deletable': True
                                }
                            )
                            break

    def get_decimal_places(self):
        return SCHEMA_COLUMN_CONFIG.get(self.source, {}).get(self.source_field, {}).get('decimal_spaces', 2)
    
    def get_formula_method(self):
        config = SCHEMA_COLUMN_CONFIG.get(self.source, {}).get(self.source_field, {})
        return config.get('formula_method')


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
        logger.debug(
            f"→ get_value called for: column='{self.column.title}', holding='{self.holding}'")
        column = self.column
        source = column.source
        field = column.source_field
        config = SCHEMA_COLUMN_CONFIG.get(
            column.source, {}).get(column.source_field)

        # Use edited value if present
        if self.is_edited and self.value is not None:
            raw = self.value
        elif source == 'calculated':
            return self.evaluate_formula(column.formula)
        else:
            field_path = config.get('field_path')
            raw = resolve_field_path(self, field_path) if field_path else None

        dtype = config.get('data_type')
        decimal_spaces = config.get('decimal_spaces', None)

        try:
            if dtype == 'decimal' and raw is not None:
                val = float(raw)
                return round(val, decimal_spaces) if decimal_spaces is not None else val
            elif dtype == 'string':
                return str(raw)
            return raw
        except (TypeError, ValueError):
            return None

    def evaluate_formula(self, formula):
        try:
            method_name = self.column.get_formula_method()
            if method_name:
                method = getattr(self.holding, method_name, None)
                if method:
                    result = method()
                    return round(float(result), self.column.get_decimal_places()) if result is not None else None
            
            if not formula:
                return None
        
            # Build context using other column values for this holding
            context = {}
            all_values = self.holding.column_values.select_related('column')

            for val in all_values:
                logger.debug(
                    f"Checking value: column={val.column.title}, source_field={val.column.source_field}, is_edited={val.is_edited}")
                field = val.column.source_field
                # skip 'calculated' to avoid recursion
                if field and val.column.source in ('holding', 'asset'):
                    # will use edited if applicable
                    context_key = field.split('.')[-1]
                    context[context_key] = val.get_value()

            if 'fx_rate' in formula:
                from_currency = self.holding.stock.currency
                to_currency = self.holding.self_managed_account.stock_portfolio.portfolio.profile.currency
                # Set this in your settings file or use a .env loader
                fx_rate = get_fx_rate(from_currency, to_currency)
                # Fallback to 1 if not available
                context['fx_rate'] = fx_rate or 1
                logger.debug(
                    f"FX: {from_currency} → {to_currency} = {fx_rate}")

            logger.debug(f"Final formula context: {context}")

            result = numexpr.evaluate(formula, local_dict=context)
            return round(float(result), self.column.get_decimal_places())
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
    
    def get_column_value(self, source_field):
        # Try to find the existing value
        val = self.column_values.select_related('column').filter(column__source_field=source_field).first()

        if not val:
            schema = self.self_managed_account.active_schema
            config = SCHEMA_COLUMN_CONFIG.get('holding', {}).get(source_field)

            if config:
                # Try to find or create the missing column
                column, created = StockPortfolioSchemaColumn.objects.get_or_create(
                    schema=schema,
                    source='holding',
                    source_field=source_field,
                    defaults={
                        'title': source_field.replace('_', ' ').title(),
                        'editable': config.get('editable', True)
                    }
                )

                # Only create the value if it doesn't already exist
                val, val_created = StockPortfolioSchemaColumnValue.objects.get_or_create(
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

        if quantity is not None and price is not None:
            return round(quantity * price, 2)
        return None
    
    def get_current_value_profile_fx(self):
        price = self.get_column_value('price')
        quantity = self.get_column_value('quantity')
        from_currency = self.stock.currency
        to_currency = self.self_managed_account.stock_portfolio.portfolio.profile.currency
        fx_rate = get_fx_rate(from_currency, to_currency)

        if price is not None and quantity is not None and fx_rate is not None:
            return round(price * quantity * fx_rate, 2)
        return None
    
    def get_unrealized_gain(self):
        quantity = self.get_column_value('quantity')
        price = self.get_column_value('price')
        purchase_price = self.get_column_value('purchase_price')

        if quantity is not None and price is not None and purchase_price is not None:
            return round((price - purchase_price) * quantity, 2)
        return None
    
    def get_unrealized_gain_profile_fx(self):
        quantity = self.get_column_value('quantity')
        price = self.get_column_value('price')
        purchase_price = self.get_column_value('purchase_price')
        from_currency = self.stock.currency
        to_currency = self.self_managed_account.stock_portfolio.portfolio.profile.currency
        fx_rate = get_fx_rate(from_currency, to_currency)

        if all(v is not None for v in [quantity, price, purchase_price, fx_rate]):
            unrealized = (price - purchase_price) * quantity * fx_rate
            return round(unrealized, 2)
        return None