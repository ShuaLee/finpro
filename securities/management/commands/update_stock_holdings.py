from django.core.management.base import BaseCommand
from securities.models import StockHolding
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Updates holding_display for all existing StockHolding instances.'

    def handle(self, *args, **options):
        holdings = StockHolding.objects.all()
        count = holdings.count()
        self.stdout.write(f"Found {count} StockHolding instances to update.")

        for holding in holdings:
            try:
                holding.sync_holding_display(save=True)
                self.stdout.write(f"Updated {holding.ticker} successfully.")
            except Exception as e:
                logger.error(f"Error updating {holding.ticker}: {str(e)}")
                self.stdout.write(self.style.ERROR(
                    f"Failed to update {holding.ticker}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(
            f"Successfully updated {count} StockHolding instances."))
