from django.core.exceptions import ValidationError
from django.db import models


class PortfolioDenomination(models.Model):
    class Kind(models.TextChoices):
        PROFILE_CURRENCY = "profile_currency", "Profile Currency"
        CURRENCY = "currency", "Currency"
        ASSET_UNITS = "asset_units", "Asset Units"

    portfolio = models.ForeignKey(
        "portfolios.Portfolio",
        on_delete=models.CASCADE,
        related_name="denominations",
    )
    key = models.SlugField(max_length=100)
    label = models.CharField(max_length=150)
    kind = models.CharField(max_length=30, choices=Kind.choices)

    currency = models.ForeignKey(
        "fx.FXCurrency",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="portfolio_denominations",
    )
    asset = models.ForeignKey(
        "assets.Asset",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="portfolio_denominations",
    )
    reference_code = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        help_text="External identifier used to resolve an asset (e.g. BTC, AAPL, GCUSD).",
    )
    unit_label = models.CharField(max_length=20, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "key"]
        constraints = [
            models.UniqueConstraint(
                fields=["portfolio", "key"],
                name="uniq_portfolio_denomination_key",
            )
        ]
        indexes = [
            models.Index(fields=["portfolio", "is_active", "display_order"]),
        ]

    def clean(self):
        super().clean()

        if self.kind == self.Kind.PROFILE_CURRENCY:
            if self.currency_id or self.asset_id:
                raise ValidationError("Profile currency denomination cannot set currency or asset.")
        elif self.kind == self.Kind.CURRENCY:
            if not self.currency_id:
                raise ValidationError("Currency denomination requires currency.")
            if self.asset_id:
                raise ValidationError("Currency denomination cannot set asset.")
        elif self.kind == self.Kind.ASSET_UNITS:
            if self.currency_id:
                raise ValidationError("Asset-units denomination cannot set currency.")
            if not self.reference_code and not self.asset_id:
                raise ValidationError("Asset-units denomination requires reference_code or asset.")
        else:
            raise ValidationError("Unsupported denomination kind.")

        if self.pk:
            original = PortfolioDenomination.objects.only("portfolio_id", "is_system").filter(pk=self.pk).first()
            if original and original.portfolio_id != self.portfolio_id:
                raise ValidationError("Denomination portfolio cannot be changed.")
            if original and original.is_system and not self.is_system:
                raise ValidationError("System denominations cannot be converted to custom.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_system:
            raise ValidationError("System denominations cannot be deleted.")
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.portfolio_id}:{self.key}"


class PortfolioValuationSnapshot(models.Model):
    portfolio = models.ForeignKey(
        "portfolios.Portfolio",
        on_delete=models.CASCADE,
        related_name="valuation_snapshots",
    )
    base_value_identifier = models.SlugField(max_length=100, default="current_value")
    profile_currency_code = models.CharField(max_length=3)
    total_value = models.DecimalField(max_digits=20, decimal_places=2)
    denominations = models.JSONField(default=list, blank=True)
    captured_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-captured_at"]
        indexes = [
            models.Index(fields=["portfolio", "-captured_at"]),
        ]

    def clean(self):
        super().clean()
        if self.pk:
            original = PortfolioValuationSnapshot.objects.only("portfolio_id").filter(pk=self.pk).first()
            if original and original.portfolio_id != self.portfolio_id:
                raise ValidationError("Snapshot portfolio cannot be changed.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.portfolio_id}:{self.total_value}:{self.captured_at}"
