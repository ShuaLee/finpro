from django.core.management.base import BaseCommand

from accounts.services.job_service import AccountJobService


class Command(BaseCommand):
    help = "Run queued account jobs (sync/reconcile/snapshot)."

    def add_arguments(self, parser):
        parser.add_argument("--max-jobs", type=int, default=25)

    def handle(self, *args, **options):
        max_jobs = options["max_jobs"]
        processed = 0

        while processed < max_jobs:
            job = AccountJobService.claim_next()
            if not job:
                break
            try:
                result = AccountJobService.execute(job)
                AccountJobService.mark_success(job=job, result=result)
                self.stdout.write(self.style.SUCCESS(f"Job {job.id} succeeded"))
            except Exception as exc:
                AccountJobService.mark_failure(job=job, error=str(exc))
                self.stdout.write(self.style.WARNING(f"Job {job.id} failed: {exc}"))
            processed += 1

        self.stdout.write(self.style.SUCCESS(f"Processed {processed} job(s)."))

