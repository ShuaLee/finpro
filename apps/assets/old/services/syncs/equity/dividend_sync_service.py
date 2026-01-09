import logging
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction

from assets.models.asset_core import Asset
from assets.models.events import EquityDividendEvent
from assets.services.syncs.base import BaseSyncService
from assets.services.utils import get_primary_ticker
from assets.services.dividends.recompute import recompute_dividend_extension
from external_data.fmp.equities.fetchers import fetch_equity_dividends
from external_data.fmp.equities.mappings import parse_dividend_event

logger = logging.getLogger(__name__)

DIVIDEND_QUANT = Decimal("0.000001")  # 6 decimal places


def _norm_decimal(val):
    if val is None:
        return None
    if not isinstance(val, Decimal):
        return val
    return val.quantize(DIVIDEND_QUANT, rounding=ROUND_HALF_UP)


class EquityDividendSyncService(BaseSyncService):
    """
    Synchronizes equity dividend history from external providers (FMP).

    Strategy:
        - Dividend events are immutable facts
        - Identity = (asset, ex_date)
        - Provider revisions update existing rows
        - New dividends are appended
        - No deletions are ever performed

    This service is safe to run repeatedly (idempotent).
    """

    @staticmethod
    @transaction.atomic
    def sync(asset: Asset) -> dict:
        ticker = get_primary_ticker(asset)
        if not ticker:
            return {"success": False, "error": "missing_ticker"}

        raw_events = fetch_equity_dividends(ticker)
        if not raw_events:
            return {"success": False, "error": "no_dividend_data"}

        added = 0
        updated = 0
        unchanged = 0

        # --------------------------------------------------
        # Process provider events (IDEMPOTENT)
        # --------------------------------------------------
        for raw in raw_events:
            parsed = parse_dividend_event(raw)

            if not parsed.get("ex_date"):
                continue  # skip malformed rows

            event, created = EquityDividendEvent.objects.get_or_create(
                asset=asset,
                ex_date=parsed["ex_date"],
                defaults=parsed,
            )

            if created:
                added += 1
                continue

            changed = False
            for field, new_value in parsed.items():
                if field == "ex_date":
                    continue

                old_value = _norm_decimal(getattr(event, field))
                new_value = _norm_decimal(new_value)

                if old_value != new_value:
                    setattr(event, field, new_value)
                    changed = True

            if changed:
                event.save()
                updated += 1
            else:
                unchanged += 1

        # --------------------------------------------------
        # Recompute derived dividend metrics (SINGLE SOURCE)
        # --------------------------------------------------
        recompute_dividend_extension(asset)

        return {
            "success": True,
            "events": {
                "added": added,
                "updated": updated,
                "unchanged": unchanged,
            },
        }
