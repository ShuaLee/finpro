from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from portfolios.models.base import BaseAssetPortfolio
from portfolios.models.portfolio import Portfolio
from schemas.models import SubPortfolioSchemaLink



class CustomPortfolio(BaseAssetPortfolio):
    """
    A user-defined sub-portfolio type (e.g., Trading Cards).
    Multiple custom portfolios per main Portfolio are allowed (e.g., cards, sneakers).
    """
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name='custom_portfolios'
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=50)

    class Meta:
        app_label = 'portfolios'
        unique_together = ('portfolio', 'slug')

    def __str__(self):
        return f"{self.portfolio.profile.user.email} | {self.name}"
    
    def clean(self):
        if not self.slug:
            self.slug = slugify(self.name or "")
        if not self.slug:
            raise ValidationError("CustomPortfolio must have a non-empty slug.")
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_schema_for_account_model(self, account_model_class):
        """
        Return the Schema object linked for this sub-portfolio + account model class.
        """
        link = (
            SubPortfolioSchemaLink.objects
            .select_related("schema")
            .filter(
                subportfolio_ct=ContentType.objects.get_for_model(self),
                subportfolio_id=self.id,
                account_model_ct=ContentType.objects.get_for_model(account_model_class),
            )
            .first()
        )
        return link.schema if link else None