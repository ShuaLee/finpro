from django.utils import timezone

from allocations.models import AllocationEvaluationRun


class AllocationRunService:
    @staticmethod
    def create_pending(*, scenario, triggered_by=None, as_of=None):
        return AllocationEvaluationRun.objects.create(
            scenario=scenario,
            status=AllocationEvaluationRun.Status.PENDING,
            triggered_by=triggered_by,
            as_of=as_of,
        )

    @staticmethod
    def mark_running(*, run):
        run.status = AllocationEvaluationRun.Status.RUNNING
        run.started_at = timezone.now()
        run.error_message = None
        run.save(update_fields=["status", "started_at", "error_message"])
        return run

    @staticmethod
    def mark_success(*, run):
        run.status = AllocationEvaluationRun.Status.SUCCESS
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "finished_at"])
        return run

    @staticmethod
    def mark_failed(*, run, error):
        run.status = AllocationEvaluationRun.Status.FAILED
        run.finished_at = timezone.now()
        run.error_message = str(error)
        run.save(update_fields=["status", "finished_at", "error_message"])
        return run
