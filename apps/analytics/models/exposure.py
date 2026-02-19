from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum


class AssetDimensionExposure(models.Model):
    """
    Weighted mapping from Asset -> Bucket for weighted dimensions.
    """

    class Source(models.TextChoices):
        SYSTEM = "system", "System"
        USER = "user", "User"

    dimension = models.ForeignKey(
        "analytics.AnalyticDimension",
        on_delete=models.CASCADE,
        related_name="asset_exposures",
    )

    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.CASCADE,
        related_name="analytic_exposures",
    )

    bucket = models.ForeignKey(
        "analytics.DimensionBucket",
        on_delete=models.CASCADE,
        related_name="asset_exposures",
    )

    weight = models.DecimalField(max_digits=9, decimal_places=6)
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.USER)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["dimension", "asset", "bucket"],
                name="uniq_asset_bucket_exposure",
            ),
            models.CheckConstraint(
                condition=models.Q(weight__gte=0) & models.Q(weight__lte=1),
                name="asset_exposure_weight_between_0_and_1",
            ),
        ]
        indexes = [
            models.Index(fields=["dimension", "asset"]),
            models.Index(fields=["dimension", "bucket"]),
        ]

    def clean(self):
        super().clean()
        if self.bucket.dimension_id != self.dimension_id:
            raise ValidationError("Bucket must belong to the same dimension.")
        if self.dimension.dimension_type != self.dimension.DimensionType.WEIGHTED:
            raise ValidationError("Asset exposures are only valid for weighted dimensions.")

        total = (
            AssetDimensionExposure.objects.filter(dimension=self.dimension, asset=self.asset)
            .exclude(pk=self.pk)
            .aggregate(total=Sum("weight"))["total"]
            or Decimal("0")
        )
        total = Decimal(str(total)) + Decimal(str(self.weight or 0))
        if total > Decimal("1"):
            raise ValidationError("Asset exposure weights per asset must not exceed 1.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.dimension.name}:{self.asset_id}->{self.bucket.key} ({self.weight})"


class HoldingDimensionExposureOverride(models.Model):
    """
    Optional holding-specific override for weighted exposures.
    """

    dimension = models.ForeignKey(
        "analytics.AnalyticDimension",
        on_delete=models.CASCADE,
        related_name="holding_exposure_overrides",
    )

    holding = models.ForeignKey(
        "accounts.Holding",
        on_delete=models.CASCADE,
        related_name="analytic_exposure_overrides",
    )

    bucket = models.ForeignKey(
        "analytics.DimensionBucket",
        on_delete=models.CASCADE,
        related_name="holding_exposure_overrides",
    )

    weight = models.DecimalField(max_digits=9, decimal_places=6)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["dimension", "holding", "bucket"],
                name="uniq_holding_bucket_exposure_override",
            ),
            models.CheckConstraint(
                condition=models.Q(weight__gte=0) & models.Q(weight__lte=1),
                name="holding_exposure_weight_between_0_and_1",
            ),
        ]
        indexes = [
            models.Index(fields=["dimension", "holding"]),
            models.Index(fields=["dimension", "bucket"]),
        ]

    def clean(self):
        super().clean()
        if self.bucket.dimension_id != self.dimension_id:
            raise ValidationError("Bucket must belong to the same dimension.")
        if self.dimension.dimension_type != self.dimension.DimensionType.WEIGHTED:
            raise ValidationError("Holding overrides are only valid for weighted dimensions.")

        if self.holding.account.portfolio_id != self.dimension.analytic.portfolio_id:
            raise ValidationError("Holding must belong to the same portfolio as the analytic.")

        total = (
            HoldingDimensionExposureOverride.objects.filter(
                dimension=self.dimension,
                holding=self.holding,
            )
            .exclude(pk=self.pk)
            .aggregate(total=Sum("weight"))["total"]
            or Decimal("0")
        )
        total = Decimal(str(total)) + Decimal(str(self.weight or 0))
        if total > Decimal("1"):
            raise ValidationError("Holding override weights per holding must not exceed 1.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.dimension.name}:{self.holding_id}->{self.bucket.key} ({self.weight})"
