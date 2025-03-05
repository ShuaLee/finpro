from django.db import models
from portfolio.models import IndividualPortfolio

# Create your models here.


class StockAccount(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('self_managed', 'Self Managed'),
        ('managed', 'Managed'),
    ]

    portfolio = models.ForeignKey(
        IndividualPortfolio, on_delete=models.CASCADE, related_name='stock_account'
    )
    account_type = models.CharField(
        max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='self_managed'
    )
    account_name = models.CharField(max_length=255, default='Stock Account')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account_name} - {self.portfolio.name}"

    class Meta:
        verbose_name = "Stock Account"
        verbose_name_plural = "Stock Account"
