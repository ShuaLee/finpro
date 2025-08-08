from django.core.exceptions import ValidationError
from django.db import models
from external_data.fx import get_fx_rate
from portfolios.models.stock import StockPortfolio
from schemas.models import Schema
from accounts.models.base import BaseAccount
from decimal import Decimal


class StockAccount(BaseAccount):
    stock_portfolio = models.ForeignKey(
        StockPortfolio,
        on_delete=models.CASCADE,
        related_name='stock_accounts'
    )

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

    account_mode = models.CharField(
        max_length=20,
        choices=[
            ("self_managed", "Self-Managed"),
            ("managed", "Managed"),
        ],
        default="self_managed"
    )

    # Managed-specific fields
    strategy = models.CharField(max_length=100, null=True, blank=True)
    current_value = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True)
    invested_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['stock_portfolio', 'name'],
                name='unique_stockaccount_name_in_portfolio'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.get_account_mode_display()})"

    def switch_mode_to(self, new_mode, force=False):
        from accounts.services.account_mode_switcher import switch_account_mode
        switch_account_mode(self, new_mode, force)

    @property
    def sub_portfolio(self):
        return self.stock_portfolio

    def is_managed(self):
        return self.account_mode == "managed"

    @property
    def active_schema(self):
        if not self.stock_portfolio:
            return None
        return (
            self.stock_portfolio.self_managed_schema
            if self.account_mode == "self_managed"
            else self.stock_portfolio.managed_schema
        )

    def get_current_value(self):
        if self.is_managed():
            return self.current_value  # Already stored in profile currency

        total = Decimal(0)
        for holding in self.holdings.all():
            value = holding.get_value_in_profile_currency()
            if value:
                total += value

        return total.quantize(Decimal("0.01"))

    def get_value_in_profile_currency(self):
        base_value = self.get_current_value()
        if base_value is None:
            return None

        from_currency = self.currency
        to_currency = self.stock_portfolio.portfolio.profile.currency

        fx = get_fx_rate(from_currency, to_currency)
        return (base_value * Decimal(str(fx or 1))).quantize(Decimal("0.01"))

    def save(self, *args, **kwargs):
        if not self.stock_portfolio:
            raise ValidationError("Stock portfolio is required.")
        if not self.active_schema:
            raise ValidationError(
                "Active schema could not be resolved from stock portfolio.")

        super().save(*args, **kwargs)

        # On creation or mode change, make sure schema visibility is synced
        if self.active_schema:
            self.initialize_visibility_settings(self.active_schema)
