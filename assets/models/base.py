from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from portfolios.models.base import InvestmentTheme
from portfolios.utils import get_fx_rate
from ..constants import ASSET_SCHEMA_CONFIG
from ..utils import get_default_for_type
from decimal import Decimal, InvalidOperation
import logging

logger = logging.getLogger(__name__)


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
        related_name='holdings'
    )

    class Meta:
        abstract = True

    @property
    def asset(self):
        """
        Must be overridden in subclasses to return the asset instance
        (e.g., Stock, RealEstate, PreciousMetal).
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement the `asset` property.")

    def get_profile_currency(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_profile_currency()")

    def get_column_value(self, source_field, *, asset_type: str, get_schema, column_model, column_value_model):
        val = self.column_values.select_related('column').filter(
            column__source_field=source_field).first()

        if not val:
            schema = get_schema()
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
                val, _ = column_value_model.objects.get_or_create(
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
        else:
            return None

    def get_current_value(self):
        """
        Default method: multiply quantity * asset price.
        Override in subclass where this doesnt apply (e.g., real estate)
        """
        try:
            quantity = self.get_column_value('quantity')
            price = self.get_column_value('price')
            if quantity is not None and price is not None:
                return round(float(quantity) * float(price), 2)
        except (TypeError, ValueError):
            pass
        return None

    def get_current_value_in_profile_fx(self):
        """
        Converts current value to profile currency using FX rate.
        This method assumes:
            - `self.asset.currency` exists.
            - `self.get_current_value()` returns value in the asset's currency.
            - `self.get_profile_currency()` is implemented in the subclass or returns the user currency.
        """
        current_value = self.get_current_value()
        from_currency = getattr(self.asset, 'currency', None)
        to_currency = self.get_profile_currency() if hasattr(
            self, 'get_profile_currency') else None

        if current_value is None or from_currency is None or to_currency is None:
            return None

        fx_rate = get_fx_rate(from_currency, to_currency)
        try:
            return round(float(current_value) * float(fx_rate), 2)
        except (TypeError, ValueError):
            return None

    def get_unrealized_gain(self):
        """
        Calculates unrealized gain: (current_price - purchase_price) * quantity.
        Falls back to None if any component is missing or invalid.
        """
        try:
            quantity = self.get_column_value('quantity')
            price = self.get_column_value('price')
            purchase_price = self.get_column_value('purchase_price')

            if None in (quantity, price, purchase_price):
                return None

            # Convert all to Decimal for accuracy
            quantity = Decimal(str(quantity))
            price = Decimal(str(price))
            purchase_price = Decimal(str(purchase_price))

            gain = (price - purchase_price) * quantity
            return round(gain, 2)
        except (InvalidOperation, TypeError, ValueError):
            return None

    def get_unrealized_gain_profile_fx(self):
        """
        Returns unrealized gain converted into the profile currency using FX rate.
        """
        base_gain = self.get_unrealized_gain()
        from_currency = getattr(self.asset, 'currency', None)

        if not hasattr(self, 'get_profile_currency'):
            logger.warning(
                f"{self.__class__.__name__} missing get_profile_currency method.")

        to_currency = self.get_profile_currency() if hasattr(
            self, 'get_profile_currency') else None

        if base_gain is None or not from_currency or not to_currency:
            return None

        try:
            fx_rate = get_fx_rate(from_currency, to_currency)
            if fx_rate in (None, 0):
                return None
            return round(Decimal(str(base_gain)) * Decimal(str(fx_rate)), 2)
        except (InvalidOperation, TypeError, ValueError):
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
        self.full_clean()
        logger.debug(
            f"Saving {self.__class__.__name__} for asset {getattr(self, 'asset', None)}")
        return super().save(*args, **kwargs)
