import uuid

from django.db import models


class EquityDirectorySnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=50, default="fmp")
    is_active = models.BooleanField(default=True)
    row_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider"],
                condition=models.Q(is_active=True),
                name="uniq_active_equity_directory_snapshot_per_provider",
            ),
        ]
        indexes = [
            models.Index(fields=["provider", "is_active"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.provider} snapshot {self.created_at:%Y-%m-%d %H:%M:%S}"


class EquityDirectoryEntry(models.Model):
    snapshot = models.ForeignKey(
        "integrations.EquityDirectorySnapshot",
        on_delete=models.CASCADE,
        related_name="entries",
    )
    symbol = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    exchange = models.CharField(max_length=100, blank=True)
    currency = models.CharField(max_length=20, blank=True)
    is_actively_traded = models.BooleanField(default=False)
    source_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["symbol"]
        constraints = [
            models.UniqueConstraint(
                fields=["snapshot", "symbol"],
                name="uniq_equity_directory_entry_per_snapshot_symbol",
            ),
        ]
        indexes = [
            models.Index(fields=["snapshot", "symbol"]),
            models.Index(fields=["snapshot", "is_actively_traded"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.symbol} - {self.name}"
