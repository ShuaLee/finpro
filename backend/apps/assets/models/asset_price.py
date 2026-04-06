from django.db import models


class AssetPrice(models.Model):
    asset = models.OneToOneField(
        "assets.Asset",
        on_delete=models.CASCADE,
        related_name="price",
    )
    price = models.DecimalField(max_digits=40, decimal_places=18)
    change = models.DecimalField(
        max_digits=40,
        decimal_places=18,
        null=True,
        blank=True,
    )
    volume = models.BigIntegerField(null=True, blank=True)
    source = models.CharField(max_length=50, default="FMP")
    as_of = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["source", "as_of"]),
        ]

    def __str__(self):
        return f"{self.asset} = {self.price} ({self.source})"
