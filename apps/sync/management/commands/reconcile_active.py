# sync/management/commands/reconcile_equities.py
from django.core.management.base import BaseCommand
from sync.services.equity.universe.reconcile_active import (
    ReconcileActiveEquitiesService,
)


class Command(BaseCommand):
    help = "Deactivate equities no longer actively traded"

    def handle(self, *args, **opts):
        service = ReconcileActiveEquitiesService()
        result = service.sync()

        self.stdout.write(self.style.SUCCESS(
            f"Checked={result['checked']} Deactivated={result['deactivated']}"
        ))
