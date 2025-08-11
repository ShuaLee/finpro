from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from common.utils.country_currency_catalog import get_common_currency_choices
from external_data.fx import get_fx_rate
from portfolios.models.stock import StockPortfolio
from schemas.models import Schema
from accounts.models.base import BaseAccount
from decimal import Decimal


class BaseStockAccount(BaseAccount):
    broker = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Brokerage platform (e.g. Robinhood, Interactive Brokers, etc.)"
    )

    tax_status = models.CharField(
        max_length=50,
        choices=[
            ('taxable', 'Taxable'),
            ('tax_deferred', 'Tax-Deferred'),
            ('tax_exempt', 'Tax-Exempt'),
        ],
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

    currency = models.CharField(
        max_length=3,
        choices=get_common_currency_choices(),
        blank=True,
        null=True
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.currency:
            derived = self.derive_profile_currency()
            if derived:
                self.currency = derived
        super().save(*args, **kwargs)


class SelfManagedAccount(BaseStockAccount):
    stock_portfolio = models.ForeignKey(
        StockPortfolio,
        on_delete=models.CASCADE,
        related_name='self_managed_accounts'
    )

    active_schema = models.ForeignKey(
        Schema,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Schema used to display stock holdings for this account."
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['stock_portfolio', 'name'],
                name='unique_selfmanagedstockaccount_name_in_portfolio'
            )
        ]

    @property
    def sub_portfolio(self):
        return self.stock_portfolio

    def get_current_value_pfx(self):
        total = Decimal(0.0)
        for holding in self.holdings.all():
            value = holding.get_current_value()
            if value is not None:
                total += Decimal(str(value))
        return round(total, 2)

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if is_new and not self.active_schema:
            if self.stock_portfolio:
                stock_ct = ContentType.objects.get_for_model(
                    self.stock_portfolio)
                schema_qs = Schema.objects.filter(
                    content_type=stock_ct,
                    object_id=self.stock_portfolio.id
                )

                if schema_qs.exists():
                    self.active_schema = schema_qs.first()
                else:
                    raise ValidationError(
                        "StockPortfolio must have at least one schema.")
            else:
                raise ValidationError("StockPortfolio is required.")

        super().save(*args, **kwargs)

        if is_new and self.active_schema:
            self.initialize_visibility_settings(self.active_schema)


class ManagedAccount(BaseStockAccount):
    stock_portfolio = models.ForeignKey(
        StockPortfolio,
        on_delete=models.CASCADE,
        related_name='managed_accounts'
    )

    active_schema = models.ForeignKey(
        Schema,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_accounts"
    )

    current_value = models.DecimalField(max_digits=12, decimal_places=2)
    invested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    strategy = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['stock_portfolio', 'name'],
                name='unique_managedaccount_name_in_portfolio'
            )
        ]

    def get_current_value_in_pfx(self):
        to_currency = self.stock_portfolio.portfolio.profile.currency
        fx = get_fx_rate(self.currency, to_currency)

        try:
            fx_decimal = Decimal(str(fx)) if fx is not None else Decimal(1)
        except:
            fx_decimal = Decimal(1)

        return round(self.current_value * fx_decimal, 2)

    def save(self, *args, **kwargs):
        if not self.currency and self.stock_portfolio and self.stock_portfolio.portfolio:
            self.currency = self.stock_portfolio.portfolio.profile.currency
        super().save(*args, **kwargs)
