from django.db import models


class AnalyticResult(models.Model):
    """
    Materialized output bucket for a single run + dimension.
    """

    run = models.ForeignKey(
        "analytics.AnalyticRun",
        on_delete=models.CASCADE,
        related_name="results",
    )

    dimension = models.ForeignKey(
        "analytics.AnalyticDimension",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="results",
    )

    bucket = models.ForeignKey(
        "analytics.DimensionBucket",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="results",
    )

    bucket_label_snapshot = models.CharField(max_length=150)

    total_value = models.DecimalField(max_digits=20, decimal_places=2)
    percentage = models.DecimalField(max_digits=9, decimal_places=6)
    holding_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["run", "dimension", "bucket_label_snapshot"],
                name="uniq_result_bucket_per_run_dimension",
            )
        ]
        ordering = ["-total_value"]
        indexes = [
            models.Index(fields=["run", "dimension"]),
        ]

    def __str__(self):
        return f"{self.run_id}:{self.bucket_label_snapshot}:{self.total_value}"
