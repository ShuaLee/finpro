from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from schemas.models import SubPortfolioSchemaLink
from portfolios.models.base import BaseAssetPortfolio
from portfolios.models.portfolio import Portfolio

class CryptoPortfolio(BaseAssetPortfolio):
    """
    Represents a crypto-specific portfolio under a main Portfolio.

    Attributes:
        portfolio (OneToOneField): Links to the main Portfolio.
    """
    portfolio = models.OneToOneField(
        Portfolio,
        on_delete=models.CASCADE,
        related_name='cryptoportfolio'
    )

    class Meta:
        app_label = 'portfolios'

    def __str__(self):
        return f"Crypto Portfolio for {self.portfolio.profile.user.email}"
    
    def clean(self):
        """
        Validates that only one CryptoPortfolio exists per Portfolio
        and ensures schemas exist when updating.
        """
        if self.pk is None and CryptoPortfolio.objects.filter(portfolio=self.portfolio).exists():
            raise ValidationError("Only one CryptoPortfolio is allowed per Portfolio.")
        
        if self.pk and not self.schemas.exists():
            raise ValidationError("CryptoPortfolio must have at least one schema.")
        
    def save(self, *args, **kwargs):
        """
        Override save to ensire model validation before saving.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def get_schema_for_account_model(self, account_model_class):
        ct = ContentType.objects.get_for_model(account_model_class)
        return (
            SubPortfolioSchemaLink.objects
            .filter(
                subportfolio_ct=ContentType.objects.get_for_model(self),
                subportfolio_id=self.id,
                account_model_ct=ct
            )
            .values_list("schema", flat=True)
            .first()
        )

