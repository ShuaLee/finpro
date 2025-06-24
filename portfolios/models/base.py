from django.db import models
from core.models import Portfolio


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


class BaseAssetPortfolio(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True