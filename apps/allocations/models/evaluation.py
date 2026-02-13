from django.db import models

from .plan import AllocationScenario
from .target import AllocationDimension, AllocationTarget


class AllocationEvaluationRun(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    scenario = models.ForeignKey(
        AllocationScenario,
        on_delete=models.CASCADE,
        related_name="runs",
    )

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    as_of = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    error_message = models.TextField(blank=True, null=True)

    triggered_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="allocation_runs",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["scenario", "-created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.scenario.name}:{self.status}:{self.created_at}"


class AllocationGapResult(models.Model):
    """
    Materialized comparison between actual and target values.
    """

    run = models.ForeignKey(
        AllocationEvaluationRun,
        on_delete=models.CASCADE,
        related_name="results",
    )

    dimension = models.ForeignKey(
        AllocationDimension,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="results",
    )

    target = models.ForeignKey(
        AllocationTarget,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="results",
    )

    bucket_label_snapshot = models.CharField(max_length=150)

    actual_value = models.DecimalField(max_digits=20, decimal_places=2)
    target_value = models.DecimalField(max_digits=20, decimal_places=2)
    gap_value = models.DecimalField(max_digits=20, decimal_places=2)

    actual_percent = models.DecimalField(max_digits=9, decimal_places=6)
    target_percent = models.DecimalField(max_digits=9, decimal_places=6)
    gap_percent = models.DecimalField(max_digits=9, decimal_places=6)

    holding_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["run", "dimension", "bucket_label_snapshot"],
                name="uniq_allocation_gap_bucket_per_run_dimension",
            )
        ]
        ordering = ["-gap_value"]
        indexes = [
            models.Index(fields=["run", "dimension"]),
        ]

    def __str__(self):
        return f"{self.run_id}:{self.bucket_label_snapshot}:{self.gap_value}"
