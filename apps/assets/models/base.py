from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from portfolios.models import Portfolio
from external_data.fx import get_fx_rate
from ..constants import ASSET_SCHEMA_CONFIG
from ..utils import get_default_for_type
from decimal import Decimal, InvalidOperation
import logging

logger = logging.getLogger(__name__)


class InvestmentTheme(models.Model):
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name='asset_tags')
    name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtags')

    class Meta:
        unique_together = ('portfolio', 'name')

    def __str__(self):
        full_path = [self.name]
        parent = self.parent
        while parent is not None:
            full_path.append(parent.name)
            parent = parent.parent
        return " > ".join(reversed(full_path))


class Asset(models.Model):
    class Meta:
        abstract = True

    def get_type(self):
        return self.__class__.__name__

    def get_price(self):
        raise NotImplementedError


class AssetHolding(models.Model):
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
    def asset(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement the `asset` property.")

    def get_profile_currency(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_profile_currency().")

    def get_asset_type(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_asset_type().")

    def get_active_schema(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_active_schema().")

    def get_column_model(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_column_model().")

    def get_column_value_model(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_column_value_model().")

    def get_column_value(self, source_field):
        """
        Retrieve or create the SchemaColumnValue for this holding.
        """
        column_model = self.get_column_model()
        value_model = self.get_column_value_model()
        schema = self.get_active_schema()
        asset_type = self.get_asset_type()

        val = self.column_values.select_related('column').filter(
            column__source_field=source_field).first()

        if not val and schema:
            config = ASSET_SCHEMA_CONFIG.get(asset_type, {}).get(
                'holding', {}).get(source_field)
            if config:
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

        if val:
            return val.get_value()
        elif hasattr(self, source_field):
            return getattr(self, source_field)
        return None

    def get_current_value(self):
        try:
            quantity = self.get_column_value('quantity')
            price = self.get_column_value('price')
            if quantity is not None and price is not None:
                return round(float(quantity) * float(price), 2)
        except (TypeError, ValueError):
            pass
        return None

    def get_current_value_in_profile_fx(self):
        current_value = self.get_current_value()
        from_currency = getattr(self.asset, 'currency', None)
        to_currency = self.get_profile_currency()

        if current_value is None or not from_currency or not to_currency:
            return None

        fx_rate = get_fx_rate(from_currency, to_currency)
        try:
            return round(float(current_value) * float(fx_rate), 2)
        except (TypeError, ValueError):
            return None

    def get_unrealized_gain(self):
        try:
            quantity = self.get_column_value('quantity')
            price = self.get_column_value('price')
            purchase_price = self.get_column_value('purchase_price')

            if None in (quantity, price, purchase_price):
                return None

            return round((Decimal(str(price)) - Decimal(str(purchase_price))) * Decimal(str(quantity)), 2)
        except (InvalidOperation, TypeError, ValueError):
            return None

    def get_unrealized_gain_profile_fx(self):
        base_gain = self.get_unrealized_gain()
        from_currency = getattr(self.asset, 'currency', None)
        to_currency = self.get_profile_currency()

        if base_gain is None or not from_currency or not to_currency:
            return None

        try:
            fx_rate = get_fx_rate(from_currency, to_currency)
            return round(float(base_gain) * float(fx_rate), 2)
        except (TypeError, ValueError):
            return None

    def clean(self):
        if self.quantity < 0:
            raise ValidationError("Quantity cannot be negative.")
        if self.purchase_price and self.purchase_price < 0:
            raise ValidationError("Purchase price cannot be negative.")
        if self.purchase_date and self.purchase_date > timezone.now():
            raise ValidationError("Purchase date cannot be in the future.")
        super().clean()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        self.full_clean()
        logger.debug(
            f"Saving {self.__class__.__name__} for asset {getattr(self, 'asset', None)}")
        super().save(*args, **kwargs)

        if is_new:
            schema = self.get_active_schema()
            value_model = self.get_column_value_model()
            if schema:
                for column in schema.columns.all():
                    value_model.objects.get_or_create(
                        column=column,
                        holding=self
                    )

    def delete(self, *args, **kwargs):
        self.column_values.all().delete()
        super().delete(*args, **kwargs)
