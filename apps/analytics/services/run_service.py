from django.utils import timezone

from analytics.models.run import AnalyticRun


class AnalyticRunService:
    @staticmethod
    def create_pending(*, analytic, triggered_by=None, as_of=None):
        return AnalyticRun.objects.create(
            analytic=analytic,
            status=AnalyticRun.Status.PENDING,
            triggered_by=triggered_by,
            as_of=as_of,
        )
    
    @staticmethod
    def mark_running(*, run):
        run.status = AnalyticRun.Status.RUNNING
        run.started_at = timezone.now()
        run.error_message = None
        run.save(update_fields=["status", "started_at", "error_message"])
        return run
    
    @staticmethod
    def mark_success(*, run):
        run.status = AnalyticRun.Status.SUCCESS
        run.finished_at = timezone.now()
        run.save(updated_fields=["status", "finished_at"])
        return run
    
    @staticmethod
    def mark_failed(*, run, error):
        run.status = AnalyticRun.Status.FAILED
        run.finished_at = timezone.now()
        run.error_message = str(error)
        run.save(update_fields=["status", "finished_at", "error_message"])
        return run