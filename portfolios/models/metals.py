from django.core.exceptions import ValidationError
from django.db import models
from core.models import Portfolio
from .base import BaseAssetPortfolio

class MetalPortfolio(BaseAssetPortfolio):
    portfolio = models.OneToOneField(
        Portfolio,
        on_delete=models.CASCADE,
        related_name='metalportfolio'
    )

    def __str__(self):
        return f"Stock Portfolio for {self.portfolio.profile.user.email}"

    def clean(self):
        if self.pk is None and MetalPortfolio.objects.filter(portfolio=self.portfolio).exists():
            raise ValidationError(
                "Only one MetalPortfolio is allowed per Portfolio.")

        if self.pk and not self.schemas.exists():
            raise ValidationError(
                "MetalPortfolio must have at least one schema.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
