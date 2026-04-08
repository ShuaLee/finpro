from django.core.management.base import BaseCommand

from apps.integrations.services import (
    ActiveEquitySyncService,
    HeldEquityReviewService,
)


class Command(BaseCommand):
    help = "Refresh the current active FMP equity list and review tracked held equities."

    def handle(self, *args, **options):
        refresh_result = ActiveEquitySyncService.refresh_from_fmp()
        review_result = HeldEquityReviewService.review_all_tracked_equities()
        self.stdout.write(self.style.SUCCESS(str({"active_list": refresh_result, "held_review": review_result})))
