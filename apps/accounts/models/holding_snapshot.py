from django.db import models


class HoldingSnapshot(models.Model):
    holding = models.ForeignKey(
        "accounts.Holding",
        on_delete=models.CASCADE,
        related_name="snapshots",
    )
    as_of = models.DateTimeField(db_index=True)
    quantity = models.DecimalField(max_digits=50, decimal_places=30)
    average_purchase_price = models.DecimalField(
        max_digits=50,
        decimal_places=30,
        null=True,
        blank=True,
    )
    price = models.DecimalField(max_digits=50, decimal_places=20, null=True, blank=True)
    value_profile_currency = models.DecimalField(max_digits=50, decimal_places=20, null=True, blank=True)
    source = models.CharField(max_length=30, default="system")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-as_of", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["holding", "as_of"],
                name="uniq_holding_snapshot_point",
            )
        ]

