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
        """
        Pull the latest dividends from FMP and update our EquityDividendEvent table.
        """
        ticker = get_primary_ticker(ticker)
        if not ticker:
            logger.warning(f"[DIVIDEND] No ticker for {asset.id}")
            return False

        raw = fetch_equity_dividends(ticker)
        if not raw:
            logger.warning(
                f"[DIVIDEND] No dividend data returned for {ticker}")
            return False

        synced_any = False

        for event_raw in raw:
            parsed = parse_dividend_event(event_raw)

            # validation
            if not parsed.get("ex_date") or not parsed.get("amount"):
                continue

            ex_date_val = parsed["ex_date"]

            existing = EquityDividendEvent.objects.filter(
                asset=asset,
                ex_date=ex_date_val
            ).first()

            if existing:
                # alreaady synced, skip
                continue

            EquityDividendEvent.objects.create(
                asset=asset,
                ex_date=ex_date_val,
                payment_date=parsed.get("payment_date"),
                declaration_date=parsed.get("declaration_date"),
                amount=parsed["amount"],
                frequency=parsed.get("frequency"),
                is_special=parsed.get("is_special", False),
            )
            synced_any = True

        # prune old history to keep storage small
        EquityDividendSyncService._cleanup_events(asset)

        # update profile yield metrics (forward & trending)
        EquityDividendSyncService._update_yield_metric(asset)

        return synced_any

    # ------------------------------------------------------------
    # CLEANUP OLD EVENTS
    # ------------------------------------------------------------
    @staticmethod
    def _update_yield_metrics(asset: Asset):
        """
        Computes:
           - trailing 12-month dividend sum
           - forward annualized dividend estimate (if determinable)
        and updates them on EquityProfile.
        """
        profile = getattr(asset, "equity_profile", None)
        if not profile:
            return

        events = list(asset.dividend_events.order_by("-ex_date")[:12])
        if not events:
            profile.trailing_dividend_12m = None
            profile.forward_dividend = None
            profile.save()
            return

        # trailing 12-month sum
        trailing_sum = sum([e.amount for e in events if not e.is_special])

        # forward projection:
        # use the most recent *non-special* event
        normal_event = next((e for e in events if not e.is_special), None)

        if normal_event:
            freq = normal_event.frequency
            amt = normal_event.amount

            multiplier = {
                "Monthly": 12,
                "Quarterly": 4,
                "SemiAnnual": 2,
                "Annual": 1,
            }.get(freq, None)

            if multiplier:
                forward = amt * multiplier
            else:
                forward = None  # Irregular/Special cannot project
        else:
            forward = None

        profile.trailing_dividend_12m = trailing_sum
        profile.forward_dividend = forward
        profile.save()
