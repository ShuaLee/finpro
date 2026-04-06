from django.core.exceptions import ValidationError
from django.db import models


class AssetMarketData(models.Model):
    class Provider(models.TextChoices):
        FMP = "fmp", "FMP"

    class Status(models.TextChoices):
        UNTRACKED = "untracked", "Untracked"
        TRACKED = "tracked", "Tracked"
        STALE = "stale", "Stale"
        UNRESOLVED = "unresolved", "Unresolved"

    asset = models.OneToOneField(
        "assets.Asset",
        on_delete=models.CASCADE,
        related_name="market_data",
    )
    provider = models.CharField(
        max_length=50,
        choices=Provider.choices,
        default=Provider.FMP,
    )
    provider_symbol = models.CharField(
        max_length=50,
        blank=True,
        help_text="Provider-facing symbol used for quotes/profile lookups.",
    )
    provider_identifier = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional stable provider identifier if available.",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UNTRACKED,
    )
    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_successful_sync_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["asset__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_symbol"],
                condition=~models.Q(provider_symbol=""),
                name="uniq_asset_market_data_provider_symbol",
            ),
            models.UniqueConstraint(
                fields=["provider", "provider_identifier"],
                condition=~models.Q(provider_identifier=""),
                name="uniq_asset_market_data_provider_identifier",
            ),
        ]
        indexes = [
            models.Index(fields=["provider", "status"]),
            models.Index(fields=["provider", "provider_symbol"]),
        ]

    @property
    def is_tracked(self) -> bool:
        return self.status == self.Status.TRACKED

    def clean(self):
        super().clean()

        self.provider_symbol = (self.provider_symbol or "").strip().upper()
        self.provider_identifier = (self.provider_identifier or "").strip()
        self.last_error = (self.last_error or "").strip()

        if self.asset.owner is not None and self.status == self.Status.TRACKED:
            # User-owned assets can still be linked later, but tracked market linkage
            # should be explicit and symbol-backed.
            if not self.provider_symbol:
                raise ValidationError(
                    {"provider_symbol": "Tracked assets must have a provider symbol."}
                )

        if self.status == self.Status.TRACKED and not self.provider_symbol:
            raise ValidationError(
                {"provider_symbol": "Tracked assets must have a provider symbol."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.asset} [{self.provider}:{self.status}]"
