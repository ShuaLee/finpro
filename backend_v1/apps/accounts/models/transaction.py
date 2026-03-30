from django.core.exceptions import ValidationError
from django.db import models


class AccountTransaction(models.Model):
    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        PLAID = "plaid", "Plaid"
        IMPORT = "import", "Import"

    class EventType(models.TextChoices):
        BUY = "buy", "Buy"
        SELL = "sell", "Sell"
        DIVIDEND = "dividend", "Dividend"
        INTEREST = "interest", "Interest"
        FEE = "fee", "Fee"
        TAX = "tax", "Tax"
        DEPOSIT = "deposit", "Deposit"
        WITHDRAWAL = "withdrawal", "Withdrawal"
        TRANSFER_IN = "transfer_in", "Transfer In"
        TRANSFER_OUT = "transfer_out", "Transfer Out"
        ADJUSTMENT = "adjustment", "Adjustment"

    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    holding = models.ForeignKey(
        "accounts.Holding",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    external_transaction_id = models.CharField(max_length=255, null=True, blank=True)

    traded_at = models.DateTimeField()
    settled_at = models.DateTimeField(null=True, blank=True)

    quantity = models.DecimalField(max_digits=50, decimal_places=20, null=True, blank=True)
    unit_price = models.DecimalField(max_digits=50, decimal_places=20, null=True, blank=True)
    gross_amount = models.DecimalField(max_digits=50, decimal_places=20, null=True, blank=True)
    fees = models.DecimalField(max_digits=50, decimal_places=20, null=True, blank=True)
    taxes = models.DecimalField(max_digits=50, decimal_places=20, null=True, blank=True)
    net_amount = models.DecimalField(max_digits=50, decimal_places=20, null=True, blank=True)

    currency = models.ForeignKey(
        "fx.FXCurrency",
        on_delete=models.PROTECT,
        related_name="account_transactions",
        null=True,
        blank=True,
    )

    note = models.CharField(max_length=500, null=True, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-traded_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["account", "source", "external_transaction_id"],
                condition=models.Q(external_transaction_id__isnull=False),
                name="uniq_account_source_external_transaction",
            )
        ]

    def clean(self):
        super().clean()

        if self.holding_id and self.holding.account_id != self.account_id:
            raise ValidationError("Transaction holding must belong to the same account.")

        if self.asset_id and self.holding_id and self.holding.asset_id != self.asset_id:
            raise ValidationError("Transaction asset must match holding asset when both are provided.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
