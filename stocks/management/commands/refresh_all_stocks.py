from django.core.management.base import BaseCommand
from stocks.models import Stock
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Refreshes all stocks with yFinance data'

    def handle(self, *args, **kwargs):
        stocks = Stock.objects.all()
        updated, failed, invalid = Stock.bulk_update_from_yfinance(stocks)
        self.stdout.write(self.style.SUCCESS(
            f"Refreshed {updated} stocks, {failed} failed, {invalid} invalid tickers."
        ))