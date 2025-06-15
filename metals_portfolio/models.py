from django.conf import settings
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models
from django.utils import timezone
from portfolio.models import Asset, Portfolio, BaseAssetPortfolio, AssetHolding
from portfolio.utils import get_fx_rate
from schemas.models import Schema, SchemaColumn, SchemaColumnValue
from stock_portfolio.utils import resolve_field_path, get_default_for_type
from .constants import METALS_SCHEMA_CONFIG
from .utils import get_precious_metal_price
from decimal import Decimal
import logging
import numexpr

logger = logging.getLogger(__name__)


# ------------------------------- SCHEMA ------------------------------ #

class MetalPortfolioSchema(Schema):
    metals_portfolio = models.ForeignKey(
        'metals_portfolio.MetalsPortfolio',
        on_delete=models.CASCADE,
        related_name='schemas'
    )

    class Meta:
        unique_together = (('metals_portfolio', 'name'))

    def delete(self, *args, **kwargs):
        if self.metals_portfolio.schemas.count() <= 1:
            raise PermissionDenied(
                "Cannot delete the last schema for a MetalsPortfolio."
            )
        super().delete(*args, **kwargs)


class MetalPortfolioSchemaColumn(SchemaColumn):

    @staticmethod
    def get_source_field_choices():
        choices = []
        for source, fields in METALS_SCHEMA_CONFIG.items():
            for source_field in fields.keys():
                if source_field is not None:
                    label = source_field.replace('_', ' ').title()
                    choices.append((source_field, label))
        return choices

    SOURCE_FIELD_CHOICES = get_source_field_choices()

    schema = models.ForeignKey(
        MetalPortfolioSchema,
        on_delete=models.CASCADE,
        related_name='columns'
    )
    source_field = models.CharField(
        max_length=100, choices=SOURCE_FIELD_CHOICES, blank=True
    )

    class Meta:
        unique_together = (('schema', 'title'))

    def __str__(self):
        return f"[{self.schema.metals_portfolio.portfolio.profile}] {self.title} ({self.source})"

    def clean(self):
        if self.source in ['asset', 'holding'] and not self.source_field:
            raise ValidationError(
                "source_field is required for asset or holding sources."
            )
        if self.source == 'calculated' and not self.formula:
            raise ValidationError(
                "formula is required for calculated sources."
            )
        if self.source == 'custom' and (self.source_field or self.formula):
            raise ValidationError(
                "custom sources should not have source_field or formula."
            )
        # Validate source_field matches source
        if self.source == 'asset' and self.source_field not in ['metal', 'price']:
            raise ValidationError("Invalid source_field for asset source")
        if self.source == 'holding' and self.source_field not in ['quantity', 'purchase_price']:
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
        config = METALS_SCHEMA_CONFIG.get(
            self.source, {}
        ).get(self.source_field)

        if config:
            self.data_type = config.get('data_type')
            self.editable = config.get('editable', True)
            if self.source == 'calculated':
                self.formula = config.get('formula', '')
            # Auto-correct title to be human-firndly from source_field
            if not self.title or self.title.strip().lower() == self.source_field.replace('_', ' ').lower():
                self.title = self.source_field.replace('_', ' ').title()

        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            holdings = PreciousMetalHolding.objects.filter(
                storage_facility__metals_portfolio=self.schema.metals_portfolio
            )
            for holding in holdings:
                MetalPortfolioSchemaColumnValue.objects.get_or_create(
                    column=self,
                    holding=holding
                )

        # Ensure dependencies for calculated fields
        if self.source == 'calculated':
            dependency_fields = METALS_SCHEMA_CONFIG.get('calculated', {}).get(
                self.source_field, {}).get('context_fields', [])

            for field in dependency_fields:
                found = self.schema.columns.filter(source_field=field).exists()
                if not found:
                    for source_key, fields in MetalPortfolioSchemaColumn.items():
                        if field in fields:
                            dep_config = fields[field]
                            MetalPortfolioSchemaColumn.objects.get_or_create(
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
        return METALS_SCHEMA_CONFIG.get(self.source, {}).get(self.source_field, {}).get('decimal_spaces', 2)

    def get_formula_method(self):
        config = METALS_SCHEMA_CONFIG.get(
            self.source, {}).get(self.source_field, {})
        return config.get('formula_method')


class MetalPortfolioSchemaColumnValue(SchemaColumnValue):
    column = models.ForeignKey(
        MetalPortfolioSchemaColumn,
        on_delete=models.CASCADE,
        related_name='values'
    )
    holding = models.ForeignKey(
        'MetalHolding',
        on_delete=models.CASCADE,
        related_name='column_values'
    )

    class Meta:
        unique_together = (('column', 'holding'))

    def clean(self):
        if self.column and self.holding:
            if self.holding.storage_facility.metals_portfolio != self.column.schema.metals_portfolio:
                raise ValidationError(
                    "MetalsHolding and MetalsPortfolioSchemaColumn must belong to the same MetalsPortfolio."
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
        source = column.source
        field = column.source_field
        config = METALS_SCHEMA_CONFIG.get(
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
            if dtype == 'decimal':
                if raw is None:
                    return 0.0
                return round(float(raw), decimal_spaces)
            elif dtype == 'string':
                return str(raw) if raw else "-"
            return raw if raw is not None else "-"
        except (TypeError, ValueError):
            return 0.0 if dtype == 'decimal' else "-"

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
                from_currency = self.holding.metal.currency
                to_currency = self.holding.storage_facility.metals_portfolio.portfolio.profile.currency
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
