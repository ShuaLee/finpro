from django.db import models
from django.core.exceptions import ValidationError
from .account import Account, AccountType


# -------------------------------
# Stock – Self-Managed
# -------------------------------
class StockSelfManagedDetails(models.Model):
    account = models.OneToOneField(
        Account, on_delete=models.CASCADE, related_name="stock_self_details"
    )
    broker = models.CharField(max_length=100, blank=True, null=True)
    tax_status = models.CharField(
        max_length=50,
        choices=[
            ('taxable', 'Taxable'),
            ('tax_deferred', 'Tax-Deferred'),
            ('tax_exempt', 'Tax-Exempt'),
        ],
        default='taxable',
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
    )

    def __str__(self):
        return f"Details for {self.account}"


# -------------------------------
# Stock – Managed
# -------------------------------
class StockManagedDetails(models.Model):
    account = models.OneToOneField(
        Account, on_delete=models.CASCADE, related_name="stock_managed_details"
    )
    current_value = models.DecimalField(max_digits=12, decimal_places=2)
    invested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    strategy = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Details for {self.account}"


# -------------------------------
# Custom – Hierarchy
# -------------------------------
MAX_CUSTOM_ACCOUNT_DEPTH = 3


class CustomAccountDetails(models.Model):
    account = models.OneToOneField(
        Account, on_delete=models.CASCADE, related_name="custom_details"
    )
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    depth = models.PositiveSmallIntegerField(default=0, editable=False)

    def clean(self):
        # Enforce max depth
        d = 0
        cur = self.parent
        while cur:
            d += 1
            if d >= MAX_CUSTOM_ACCOUNT_DEPTH:
                raise ValidationError(
                    f"Maximum account depth is {MAX_CUSTOM_ACCOUNT_DEPTH}"
                )
            cur = cur.parent
        self.depth = d

    def __str__(self):
        return f"Custom hierarchy for {self.account}"
