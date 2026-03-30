from django.db import models


class ReconciliationIssue(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RESOLVED = "resolved", "Resolved"
        IGNORED = "ignored", "Ignored"

    class Severity(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        CRITICAL = "critical", "Critical"

    class IssueCode(models.TextChoices):
        MISSING_INTERNAL_HOLDING = "missing_internal_holding", "Missing Internal Holding"
        MISSING_EXTERNAL_HOLDING = "missing_external_holding", "Missing External Holding"
        QUANTITY_MISMATCH = "quantity_mismatch", "Quantity Mismatch"
        SYMBOL_UNMAPPED = "symbol_unmapped", "Symbol Unmapped"
        STALE_SYNC = "stale_sync", "Stale Sync"

    class ResolutionAction(models.TextChoices):
        KEEP_INTERNAL = "keep_internal", "Keep Internal"
        ALIGN_TO_EXTERNAL = "align_to_external", "Align To External"
        ADJUST_INTERNAL_QUANTITY = "adjust_internal_quantity", "Adjust Internal Quantity"
        IGNORE = "ignore", "Ignore"

    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        related_name="reconciliation_issues",
    )
    connection = models.ForeignKey(
        "accounts.BrokerageConnection",
        on_delete=models.CASCADE,
        related_name="reconciliation_issues",
        null=True,
        blank=True,
    )
    holding = models.ForeignKey(
        "accounts.Holding",
        on_delete=models.SET_NULL,
        related_name="reconciliation_issues",
        null=True,
        blank=True,
    )
    issue_code = models.CharField(max_length=50, choices=IssueCode.choices)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.WARNING)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    message = models.CharField(max_length=500)
    metadata = models.JSONField(default=dict, blank=True)
    resolution_action = models.CharField(
        max_length=40,
        choices=ResolutionAction.choices,
        null=True,
        blank=True,
    )
    resolution_note = models.CharField(max_length=500, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
