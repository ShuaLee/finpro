from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from accounts.models import AccountJob

from .brokerage_adapters import get_adapter
from .brokerage_sync_service import BrokerageSyncService
from .reconciliation_service import ReconciliationService
from .snapshot_service import HoldingSnapshotService
from .transaction_service import TransactionService


class AccountJobService:
    @staticmethod
    @transaction.atomic
    def enqueue(
        *,
        account,
        job_type: str,
        connection=None,
        payload: dict | None = None,
        idempotency_key: str | None = None,
        run_after=None,
    ):
        payload = payload or {}
        if idempotency_key:
            existing = AccountJob.objects.filter(
                account=account,
                job_type=job_type,
                idempotency_key=idempotency_key,
                status__in=[AccountJob.Status.PENDING, AccountJob.Status.RUNNING, AccountJob.Status.SUCCEEDED],
            ).first()
            if existing:
                return existing

        return AccountJob.objects.create(
            account=account,
            connection=connection,
            job_type=job_type,
            payload=payload,
            idempotency_key=idempotency_key,
            run_after=run_after,
        )

    @staticmethod
    @transaction.atomic
    def claim_next():
        now = timezone.now()
        job = (
            AccountJob.objects.select_for_update(skip_locked=True)
            .filter(
                status=AccountJob.Status.PENDING,
            )
            .filter(
                Q(run_after__isnull=True) | Q(run_after__lte=now)
            )
            .order_by("created_at", "id")
            .first()
        )
        if not job:
            return None
        job.status = AccountJob.Status.RUNNING
        job.started_at = now
        job.attempts += 1
        job.save(update_fields=["status", "started_at", "attempts", "updated_at"])
        return job

    @staticmethod
    @transaction.atomic
    def mark_success(*, job: AccountJob, result: dict | None = None):
        job.status = AccountJob.Status.SUCCEEDED
        job.result = result or {}
        job.error = None
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "result", "error", "finished_at", "updated_at"])
        return job

    @staticmethod
    @transaction.atomic
    def mark_failure(*, job: AccountJob, error: str):
        retryable = job.attempts < job.max_attempts
        job.status = AccountJob.Status.PENDING if retryable else AccountJob.Status.FAILED
        job.error = error
        if retryable:
            job.run_after = timezone.now() + timezone.timedelta(minutes=min(5 * job.attempts, 60))
        else:
            job.finished_at = timezone.now()
        job.save(update_fields=["status", "error", "run_after", "finished_at", "updated_at"])
        return job

    @staticmethod
    def execute(job: AccountJob) -> dict:
        account = job.account
        payload = job.payload or {}

        if job.job_type == AccountJob.JobType.SYNC_POSITIONS:
            if not job.connection:
                raise ValueError("SYNC_POSITIONS requires connection.")
            return BrokerageSyncService.sync_connection(
                connection=job.connection,
                prune_missing=bool(payload.get("prune_missing", False)),
            )

        if job.job_type == AccountJob.JobType.SYNC_TRANSACTIONS:
            if not job.connection:
                raise ValueError("SYNC_TRANSACTIONS requires connection.")
            adapter = get_adapter(job.connection.provider)
            rows = adapter.fetch_transactions(job.connection, days=int(payload.get("days", 30)))
            return TransactionService.ingest_external(
                account=account,
                source="plaid" if job.connection.provider == "plaid" else "import",
                payload_rows=rows,
            )

        if job.job_type == AccountJob.JobType.RECONCILE:
            if not job.connection:
                raise ValueError("RECONCILE requires connection.")
            adapter = get_adapter(job.connection.provider)
            positions = adapter.fetch_positions(job.connection)
            return ReconciliationService.reconcile_positions(
                connection=job.connection,
                external_positions=[{"symbol": p.symbol, "quantity": str(p.quantity)} for p in positions],
            )

        if job.job_type == AccountJob.JobType.SNAPSHOT:
            snaps = HoldingSnapshotService.capture_account(account=account, source="job")
            return {"snapshots": len(snaps)}

        raise ValueError(f"Unsupported job_type: {job.job_type}")
