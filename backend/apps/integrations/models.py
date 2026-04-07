from django.db import models


class ActiveEquityListing(models.Model):
    provider = models.CharField(max_length=50, default="fmp")
    symbol = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    source_payload = models.JSONField(default=dict, blank=True)
    last_refreshed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["symbol"]
        indexes = [
            models.Index(fields=["provider", "symbol"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.symbol} - {self.name}"
