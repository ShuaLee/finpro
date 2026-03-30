from django.db import models


class AccountJob(models.Model):
    class JobType(models.TextChoices):
        SYNC_POSITIONS = "sync_positions", "Sync Positions"
        SYNC_TRANSACTIONS = "sync_transactions", "Sync Transactions"
        RECONCILE = "reconcile", "Reconcile"
        SNAPSHOT = "snapshot", "Snapshot"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        related_name="jobs",
    )
    connection = models.ForeignKey(
        "accounts.BrokerageConnection",
        on_delete=models.CASCADE,
        related_name="jobs",
        null=True,
        blank=True,
    )
    job_type = models.CharField(max_length=40, choices=JobType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    idempotency_key = models.CharField(max_length=255, null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    result = models.JSONField(default=dict, blank=True)
    error = models.TextField(null=True, blank=True)
    run_after = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["account", "job_type", "idempotency_key"],
                condition=models.Q(idempotency_key__isnull=False),
                name="uniq_account_job_idempotency",
            )
        ]

