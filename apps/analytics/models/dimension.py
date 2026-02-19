from django.core.exceptions import ValidationError
from django.db import models


class AnalyticDimension(models.Model):
    class DimensionType(models.TextChoices):
        CATEGORICAL = "categorical", "Categorical"
        WEIGHTED = "weighted", "Weighted"

    class SourceType(models.TextChoices):
        SCV_IDENTIFIER = "scv_identifier", "SCV Identifier"
        ASSET_EXPOSURE = "asset_exposure", "Asset Exposure"
        HOLDING_EXPOSURE = "holding_exposure", "Holding Exposure"

    analytic = models.ForeignKey(
        "analytics.Analytic",
        on_delete=models.CASCADE,
        related_name="dimensions",
    )

    name = models.SlugField(max_length=100)
    label = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)

    dimension_type = models.CharField(
        max_length=20,
        choices=DimensionType.choices,
        default=DimensionType.CATEGORICAL,
    )

    source_type = models.CharField(
        max_length=30,
        choices=SourceType.choices,
        default=SourceType.SCV_IDENTIFIER,
    )

    source_identifier = models.SlugField(max_length=100, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["analytic", "name"],
                name="uniq_dimension_name_per_analytic",
            )
        ]
        ordering = ["display_order", "name"]
        indexes = [models.Index(fields=["analytic", "is_active", "display_order"]) ]

    def clean(self):
        super().clean()
        if self.dimension_type == self.DimensionType.CATEGORICAL:
            if self.source_type != self.SourceType.SCV_IDENTIFIER:
                raise ValidationError("Categorical dimensions must use source_type='scv_identifier'.")
            if not self.source_identifier:
                raise ValidationError("source_identifier is required for categorical dimensions.")
        else:
            if self.source_type == self.SourceType.SCV_IDENTIFIER:
                raise ValidationError("Weighted dimensions cannot use source_type='scv_identifier'.")
            if self.source_identifier:
                raise ValidationError("source_identifier must be empty for weighted dimensions.")

        if self.pk:
            original = AnalyticDimension.objects.only("analytic_id").filter(pk=self.pk).first()
            if original and original.analytic_id != self.analytic_id:
                raise ValidationError("Dimension analytic cannot be changed.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.analytic.name}:{self.name}"


class DimensionBucket(models.Model):
    """
    Bucket options inside a dimension.
    """

    dimension = models.ForeignKey(
        "analytics.AnalyticDimension",
        on_delete=models.CASCADE,
        related_name="buckets",
    )

    key = models.SlugField(max_length=100)
    label = models.CharField(max_length=150)

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )

    is_unknown_bucket = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["dimension", "key"],
                name="uniq_bucket_key_per_dimension",
            )
        ]
        ordering = ["display_order", "label"]
        indexes = [models.Index(fields=["dimension", "is_active", "display_order"]) ]

    def clean(self):
        super().clean()

        if self.parent and self.parent.dimension_id != self.dimension_id:
            raise ValidationError("Bucket parent must belong to the same dimension.")

        if self.pk:
            original = DimensionBucket.objects.only("dimension_id").filter(pk=self.pk).first()
            if original and original.dimension_id != self.dimension_id:
                raise ValidationError("Bucket dimension cannot be changed.")

        if self.is_unknown_bucket:
            qs = DimensionBucket.objects.filter(dimension=self.dimension, is_unknown_bucket=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("Only one unknown bucket is allowed per dimension.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.dimension.name}:{self.label}"
