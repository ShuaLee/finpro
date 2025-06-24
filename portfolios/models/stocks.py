from django.core.exceptions import ValidationError
from django.db import models
from core.models import Portfolio
from .base import BaseAssetPortfolio

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

        if self.pk and not self.schemas.exists():
            raise ValidationError(
                "StockPortfolio must have at least one schema.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
