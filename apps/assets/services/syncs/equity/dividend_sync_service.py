from django.utils.timezone import now

from assets.services.syncs.base import BaseSyncService


class EquityDividendSyncService(BaseSyncService):

    MAX_EVENTS_TO_KEEP = 24

    def sync(self, asset):
        """
        Pull the latest dividends from FMP and update our EquityDividendEvent table.
        """
        symbol = asset.primary_identifier.value
