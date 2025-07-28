from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from portfolios.models.portfolio import Portfolio
from external_data.fx import get_fx_rate
from assets.services import HoldingSchemaEngine, get_asset_schema_config
from assets.utils import get_default_for_type
from decimal import Decimal, InvalidOperation
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class InvestmentTheme(models.Model):
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name='asset_tags')
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtags')

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


class Asset(models.Model):
    """Abstract base model for all assets (e.g., Stock, Metal)."""
    class Meta:
        abstract = True

    def get_type(self):
        return self.__class__.__name__

    @abstractmethod
    def get_price(self):
        raise NotImplementedError("Subclasses must implement get_price().")


class AssetHolding(models.Model, ABC):
    """Abstract base for all asset holdings (e.g., StockHolding)."""
    quantity = models.DecimalField(max_digits=15, decimal_places=4)
    purchase_price = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True)
    purchase_date = models.DateTimeField(null=True, blank=True)
    investment_theme = models.ForeignKey(
        InvestmentTheme,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_investments'
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
        """
        schema = self.get_active_schema()
        if not schema:
            return getattr(self, source_field, None)

        val = self.column_values.select_related('column').filter(
            column__source_field=source_field
        ).first()

        if val is None:
            config = get_asset_schema_config(self.get_asset_type()).get(
                'holding', {}).get(source_field)
            if config:
                column_model = self.get_column_model()
                value_model = self.get_column_value_model()
                column, _ = column_model.objects.get_or_create(
                    schema=schema,
                    source='holding',
                    source_field=source_field,
                    defaults={
                        'title': source_field.replace('_', ' ').title(),
                        'editable': config.get('editable', True),
                    }
                )
                val, _ = value_model.objects.get_or_create(
                    column=column,
                    holding=self,
                    defaults={
                        'value': get_default_for_type(config.get('data_type')),
                        'is_edited': False,
                    }
                )

        return val.get_value() if val else getattr(self, source_field, None)

    # --- Financial calculations ---
    def get_current_value(self):
        try:
            quantity = Decimal(str(self.get_column_value('quantity') or 0))
            price = Decimal(str(self.get_column_value('price') or 0))
            return (quantity * price).quantize(Decimal('0.01'))
        except (InvalidOperation, TypeError):
            return None

    def get_current_value_in_profile_fx(self):
        value = self.get_current_value()
        if not value:
            return None

        fx_rate = get_fx_rate(
            getattr(self.asset, 'currency', None), self.get_profile_currency())
        try:
            return (value * Decimal(str(fx_rate))).quantize(Decimal('0.01'))
        except (InvalidOperation, TypeError):
            return None

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
                getattr(self.asset, 'currency', None), self.get_profile_currency())
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
        logger.debug("Saving %s for asset %s",
                     self.__class__.__name__, getattr(self, 'asset', None))

        super().save(*args, **kwargs)

        if is_new:
            schema = self.get_active_schema()
            if schema:
                engine = HoldingSchemaEngine(self, self.get_asset_type())
                engine.sync_all_columns()

    def delete(self, *args, **kwargs):
        self.column_values.all().delete()
        super().delete(*args, **kwargs)
