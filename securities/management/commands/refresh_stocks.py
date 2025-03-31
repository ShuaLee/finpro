from django.core.management.base import BaseCommand
from securities.models import Stock
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Refreshes all stock data from Yahoo Finance'

    def handle(self, *args, **options):
        stocks = Stock.objects.all()
        total_stocks = stocks.count()
        if total_stocks == 0:
            logger.info("No stocks found in the database to refresh.")
            self.stdout.write(self.style.WARNING("No stocks to refresh."))
            return

        logger.info(f"Starting refresh for {total_stocks} stocks.")
        updated = 0
        failed = 0

        for stock in stocks:
            try:
                stock.fetch_yfinance_data(force_update=True)
                updated += 1
                logger.debug(f"Successfully refreshed {stock.ticker}")
            except Exception as e:
                failed += 1
                logger.error(f"Failed to refresh {stock.ticker}: {str(e)}")

        logger.info(f"Refresh complete: {updated} updated, {failed} failed.")
        self.stdout.write(self.style.SUCCESS(
            f"Refreshed {updated} stocks, {failed} failed."))
