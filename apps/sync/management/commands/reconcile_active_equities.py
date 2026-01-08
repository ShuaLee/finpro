from django.core.management.base import BaseCommand

from sync.services.syncs.equity.universe.reconcile_active import (
    ReconcileActiveEquitiesService,
)


class Command(BaseCommand):
    help = "Reconcile actively traded equities (deactivate missing tickers only)"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                "[RECONCILE_EQUITIES] Reconciling active equities..."
            )
        )

        service = ReconcileActiveEquitiesService()
        result = service.sync()

        self.stdout.write(self.style.SUCCESS("[RECONCILE_EQUITIES] Completed"))
        self.stdout.write(
            f"  Checked: {result['checked']}\n"
            f"  Deactivated: {result['deactivated']}\n"
            f"  Provider count: {result['provider_count']}"
        )
