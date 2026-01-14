from django.db import models
from django.core.exceptions import ValidationError

from assets.models.real_estate.real_estate import RealEstateAsset


class RealEstateCashflow(models.Model):
    """
    Cashflow behaviour specific to real estate assets.

    Mirrors EquityDividendSnapshot conceptually.
    """

    real_estate = models.OneToOneField(
        RealEstateAsset,
        on_delete=models.CASCADE,
        related_name="cashflow",
    )

    # -------------------------
    # Rental behaviour
    # -------------------------
    generates_income = models.BooleanField(
        default=False,
        help_text="True if the property generates rental income."
    )

    gross_annual_rent = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
    )

    vacancy_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Expected vacancy percentage (0–100)."
    )

    # -------------------------
    # Expenses
    # -------------------------
    annual_operating_expenses = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0,
    )

    annual_property_tax = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0,
    )

    annual_insurance = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0,
    )

    # -------------------------
    # Derived metrics
    # -------------------------
    @property
    def net_annual_cashflow(self):
        if not self.generates_income:
            return 0

        effective_rent = (
            (self.gross_annual_rent or 0)
            * (1 - self.vacancy_rate / 100)
        )

        expenses = (
            self.annual_operating_expenses
            + self.annual_property_tax
            + self.annual_insurance
        )

        return effective_rent - expenses

    # -------------------------
    # Validation
    # -------------------------
    def clean(self):
        if self.generates_income and not self.gross_annual_rent:
            raise ValidationError(
                "Income-generating properties must define gross annual rent."
            )

        if self.vacancy_rate < 0 or self.vacancy_rate > 100:
            raise ValidationError(
                "Vacancy rate must be between 0 and 100."
            )

    def __str__(self):
        return f"Cashflow for {self.real_estate_id}"