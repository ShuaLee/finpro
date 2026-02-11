from django.core.exceptions import ValidationError
from django.db import models

class AnalyticalDimension(models.Model):
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

    # Used when source_type == scv_identifier
    source_identifier = models.SlugField(
        max_length=100,
        blank=True,
        null=True,
    )

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

    def clean(self):
        super().clean()
        if (
            self.source_type == self.SourceType.SCV_IDENTIFIER
            and not self.source_identifier
        ):
            raise ValidationError(
                "source_identifier is required when source_type='scv_identifier'."
            )

    def __str__(self):
        return f"{self.analytic.name}:{self.name}"
    
    
class DimensionBucket(models.Model):
    """
    Bucket options inside a dimension.
    Example: coal -> coking coal / thermal coal (parent-child hierarchy).
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
            ),
            models.UniqueConstraint(
                fields=["dimension"],
                condition=models.Q(is_unknown_bucket=True),
                name="uniq_unknown_bucket_per_dimension",
            ),
        ]
        ordering = ["display_order", "label"]

    def clean(self):
        super().clean()
        if self.parent and self.parent.dimension_id != self.dimension_id:
            raise ValidationError("Bucket parent must belong to the same dimension.")

    def __str__(self):
        return f"{self.dimension.name}:{self.label}"