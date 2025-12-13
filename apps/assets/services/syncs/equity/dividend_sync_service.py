import logging

from django.db import transaction

from assets.models.asset_core import Asset
from assets.models.events import EquityDividendEvent
from assets.services.syncs.base import BaseSyncService
from assets.services.utils import get_primary_ticker
from external_data.fmp.equities.fetchers import fetch_equity_dividends
from external_data.fmp.equities.mappings import parse_dividend_event

logger = logging.getLogger(__name__)


class EquityDividendSyncService(BaseSyncService):
    """
    Syncs raw dividend events for an equity:
      - Fetches FMP dividends
      - Normalizes & inserts missing events
      - Keeps last N events
      - Updates trailing & forward dividend info on EquityProfile
    """

    MAX_EVENTS_TO_KEEP = 24

    @staticmethod
    @transaction.atomic
    def sync(asset: Asset) -> bool:

        ticker = get_primary_ticker(asset)
        if not ticker:
            logger.warning(f"[DIVIDEND] No ticker for asset {asset.id}")
            return False

        raw_events = fetch_equity_dividends(ticker)
        if not raw_events:
            logger.warning(f"[DIVIDEND] No div data for {ticker}")
            return False

        synced_any = False

        # --------------------------------------------
        # PRELOAD EXISTING EVENTS TO AVOID DUPLICATES
        # --------------------------------------------
        existing_events = set(
            EquityDividendEvent.objects
            .filter(asset=asset)
            .values_list("ex_date", "amount", "is_special", "frequency")
        )

        # --------------------------------------------
        # PROCESS ALL EVENTS (OLD → NEW)
        # --------------------------------------------
        for raw in reversed(raw_events):
            parsed = parse_dividend_event(raw)

            ex_date = parsed.get("ex_date")
            amount = parsed.get("amount")
            freq = parsed.get("frequency")
            is_special = parsed.get("is_special", False)

            if not ex_date or not amount:
                continue

            signature = (ex_date, amount, is_special, freq)

            # Skip if already present
            if signature in existing_events:
                continue

            # Insert new event
            EquityDividendEvent.objects.create(
                asset=asset,
                ex_date=ex_date,
                payment_date=parsed.get("payment_date"),
                declaration_date=parsed.get("declaration_date"),
                amount=amount,
                frequency=freq,
                is_special=is_special,
            )

            existing_events.add(signature)
            synced_any = True

        # --------------------------------------------
        # PRUNE OLD EVENTS
        # --------------------------------------------
        EquityDividendSyncService._cleanup_events(asset)

        # --------------------------------------------
        # UPDATE FORWARD + TRAILING YIELDS
        # --------------------------------------------
        EquityDividendSyncService._update_yield_metrics(asset)

        return synced_any

    # ------------------------------------------------------------
    # CLEANUP
    # ------------------------------------------------------------

    @staticmethod
    def _cleanup_events(asset: Asset):
        events = list(asset.dividend_events.order_by("-ex_date"))
        if len(events) <= EquityDividendSyncService.MAX_EVENTS_TO_KEEP:
            return

        to_delete = events[EquityDividendSyncService.MAX_EVENTS_TO_KEEP:]
        ids = [e.id for e in to_delete]
        EquityDividendEvent.objects.filter(id__in=ids).delete()

    # ------------------------------------------------------------
    # YIELD CALCULATIONS
    # ------------------------------------------------------------
    @staticmethod
    def _update_yield_metrics(asset: Asset):
        profile = getattr(asset, "equity_profile", None)
        if not profile:
            return

        events = list(asset.dividend_events.order_by("-ex_date")[:12])

        if not events:
            profile.trailing_dividend_12m = None
            profile.forward_dividend = None
            profile.save()
            return

        # Trailing (EXCLUDES specials)
        trailing_sum = sum(
            e.amount for e in events
            if not e.is_special
        )

        # Forward: most recent NON-SPECIAL event
        normal = next((e for e in events if not e.is_special), None)

        forward = None
        if normal:
            mult = {
                "Monthly": 12,
                "Quarterly": 4,
                "SemiAnnual": 2,
                "Annual": 1,
            }.get(normal.frequency)
            if mult:
                forward = normal.amount * mult

        profile.trailing_dividend_12m = trailing_sum
        profile.forward_dividend = forward
        profile.save()
