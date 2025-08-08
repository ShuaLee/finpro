from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from portfolios.models.portfolio import Portfolio
from external_data.fx import get_fx_rate
from assets.utils import get_default_for_type
from decimal import Decimal, InvalidOperation
import logging
from abc import abstractmethod

logger = logging.getLogger(__name__)


class InvestmentTheme(models.Model):
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name='asset_tags'
    )
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtags'
    )

    class Meta:
        unique_together = ('portfolio', 'name')

    def __str__(self):
        # Full hierarchy display
        full_path = [self.name]
        parent = self.parent
        while parent:
            full_path.append(parent.name)
            parent = parent.parent
        return " > ".join(reversed(full_path))


class HoldingThemeValue(models.Model):
    holding_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    holding_id = models.PositiveIntegerField()
    holding = GenericForeignKey("holding_ct", "holding_id")

    theme = models.ForeignKey(InvestmentTheme, on_delete=models.CASCADE)

    # Support various value types (same as SchemaColumnValue)
    value_string = models.CharField(max_length=255, null=True, blank=True)
    value_decimal = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True
    )
    value_integer = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("holding_ct", "holding_id", "theme")

    def get_value(self):
        return self.value_string or self.value_decimal or self.value_integer

    def set_value(self, raw_value, data_type):
        if data_type == "decimal":
            self.value_decimal = raw_value
        elif data_type == "integer":
            self.value_integer = raw_value
        elif data_type == "string":
            self.value_string = raw_value


class Asset(models.Model):
    """Abstract base model for all assets (e.g., Stock, Metal)."""
    class Meta:
        abstract = True

    def get_type(self):
        return self.__class__.__name__

    @abstractmethod
    def get_price(self):
        raise NotImplementedError("Subclasses must implement get_price().")


class AssetHolding(models.Model):
    """Abstract base for all asset holdings (e.g., StockHolding)."""
    quantity = models.DecimalField(max_digits=15, decimal_places=4)
    purchase_price = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    purchase_date = models.DateTimeField(null=True, blank=True)

    investment_theme = models.ManyToManyField(
        InvestmentTheme,
        blank=True,
        related_name='%(class)s_investments'
    )

    # Use string ref to avoid importing schemas.models at import time
    column_values = GenericRelation(
        'schemas.SchemaColumnValue',
        content_type_field='account_ct',
        object_id_field='account_id',
        related_query_name='holding'
    )

    class Meta:
        abstract = True

    @property
    @abstractmethod
    def asset(self):
        """Return the related asset object (e.g., Stock instance)."""
        pass

    @abstractmethod
    def get_profile_currency(self):
        pass

    @abstractmethod
    def get_asset_type(self):
        pass

    @abstractmethod
    def get_active_schema(self):
        pass

    @abstractmethod
    def get_column_model(self):
        pass

    @abstractmethod
    def get_column_value_model(self):
        pass

    def get_column_value(self, source_field):
        """
        Get or create SchemaColumnValue for a given source field.
        Falls back to instance attribute if schema/column not found.
        Handles theme-backed columns via HoldingThemeValue.
        """
        schema = self.get_active_schema()
        if not schema:
            return getattr(self, source_field, None)

        column = schema.columns.filter(source_field=source_field).first()
        if not column:
            return getattr(self, source_field, None)

        # If this column is linked to a theme, fetch from HoldingThemeValue
        if getattr(column, 'investment_theme_id', None):
            htv = HoldingThemeValue.objects.filter(
                holding_ct=ContentType.objects.get_for_model(self.__class__),
                holding_id=self.id,
                theme=column.investment_theme_id
            ).select_related('theme').first()
            return htv.get_value() if htv else None

        # Otherwise, check if a SchemaColumnValue exists
        val = self.column_values.select_related('column').filter(
            column=column
        ).first()

        if val is None:
            # Lazy import here to avoid circular import at module load
            from schemas.config.utils import get_asset_schema_config

            config = (get_asset_schema_config(self.get_asset_type())
                      .get('holding', {})
                      .get(source_field))
            if config:
                value_model = self.get_column_value_model()
                val, _ = value_model.objects.get_or_create(
                    column=column,
                    account_id=self.id,
                    account_ct=ContentType.objects.get_for_model(
                        self.__class__),
                    defaults={
                        'value': get_default_for_type(config.get('data_type')),
                        'is_edited': False,
                    }
                )

        return val.get_value() if val else getattr(self, source_field, None)

    # --- Financial calculations ---
    def get_value_in_asset_currency(self):
        try:
            quantity = Decimal(str(self.get_column_value('quantity') or 0))
            price = Decimal(str(self.get_column_value('price') or 0))
            return (quantity * price).quantize(Decimal('0.01'))
        except (InvalidOperation, TypeError):
            return None

    def get_value_in_profile_currency(self):
        base_value = self.get_value_in_asset_currency()
        if base_value is None:
            return None

        from_currency = getattr(self.asset, 'currency', 'USD') or 'USD'
        to_currency = self.get_profile_currency()

        fx = get_fx_rate(from_currency, to_currency)
        return (base_value * Decimal(str(fx or 1))).quantize(Decimal("0.01"))

    def get_unrealized_gain(self):
        try:
            quantity = Decimal(str(self.get_column_value('quantity') or 0))
            price = Decimal(str(self.get_column_value('price') or 0))
            purchase_price = Decimal(
                str(self.get_column_value('purchase_price') or 0))
            return ((price - purchase_price) * quantity).quantize(Decimal('0.01'))
        except (InvalidOperation, TypeError):
            return None

    def get_unrealized_gain_profile_fx(self):
        base_gain = self.get_unrealized_gain()
        if not base_gain:
            return None
        try:
            fx_rate = get_fx_rate(
                getattr(self.asset, 'currency',
                        None), self.get_profile_currency()
            )
            return (base_gain * Decimal(str(fx_rate))).quantize(Decimal('0.01'))
        except (InvalidOperation, TypeError):
            return None

    # --- Validation ---
    def clean(self):
        if self.quantity < 0:
            raise ValidationError("Quantity cannot be negative.")
        if self.purchase_price and self.purchase_price < 0:
            raise ValidationError("Purchase price cannot be negative.")
        if self.purchase_date and self.purchase_date > timezone.now():
            raise ValidationError("Purchase date cannot be in the future.")
        super().clean()

    # --- Save/Delete with related updates ---
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        self.full_clean()
        print(
            f"💾 Saving {self.__class__.__name__} for asset {getattr(self, 'asset', None)}")

        super().save(*args, **kwargs)

        if is_new:
            print("🛠 New holding detected. Attempting schema sync...")
            schema = self.get_active_schema()
            if schema:
                print(f"📐 Schema found: {schema}")
                # Lazy import to avoid circular dependency
                from schemas.services.holding_sync_service import HoldingSchemaEngine
                engine = HoldingSchemaEngine(self, self.get_asset_type())
                engine.sync_all_columns()
            else:
                print("⚠️ No schema found. Skipping sync.")

    def delete(self, *args, **kwargs):
        self.column_values.all().delete()
        super().delete(*args, **kwargs)
