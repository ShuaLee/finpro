import logging

from django.db import transaction

from assets.models.asset_core import Asset, AssetIdentifier
from assets.models.events.equity import EquityDividendEvent
from external_data.exceptions import ExternalDataEmptyResult, ExternalDataError
from external_data.providers.fmp.client import FMP_PROVIDER
from sync.services.base import BaseSyncService
from assets.services.dividends.recompute import recompute_dividend_extension

logger = logging.getLogger(__name__)


class EquityDividendSyncService(BaseSyncService):
    """
    Synchronizes historical dividend events for an equity.

    Guarantees:
    - Events are immutable facts keyed by (asset, ex_date)
    - Provider revisions update existing rows
    - New dividends are appended
    - No deletions are ever performed
    """

    name = "equity.dividends"

    @transaction.atomic
    def _sync(self, asset: Asset) -> dict:
        ticker = self._get_ticker(asset)
        if not ticker:
            return {"success": False, "error": "missing_ticker"}

        try:
            raw_events = FMP_PROVIDER.get_equity_dividends(ticker)
        except ExternalDataEmptyResult:
            # No dividends is valid
            raw_events = []
        except ExternalDataError:
            raise

        added = 0
        updated = 0
        unchanged = 0

        for raw in raw_events:
            ex_date = raw.get("ex_date")
            if not ex_date:
                continue  # malformed row

            event, created = EquityDividendEvent.objects.get_or_create(
                asset=asset,
                ex_date=ex_date,
                defaults=self._event_defaults(raw),
            )

            if created:
                added += 1
                continue

            # Provider revision handling
            changed = False
            for field, value in self._event_defaults(raw).items():
                old = getattr(event, field)
                if old != value:
                    setattr(event, field, value)
                    changed = True

            if changed:
                event.save()
                updated += 1
            else:
                unchanged += 1

        # Recompute derived metrics
        recompute_dividend_extension(asset)

        logger.info(
            "[DIVIDEND_SYNC] %s | added=%s updated=%s unchanged=%s",
            ticker,
            added,
            updated,
            unchanged,
        )

        return {
            "success": True,
            "events": {
                "added": added,
                "updated": updated,
                "unchanged": unchanged,
            },
        }

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def _get_ticker(self, asset: Asset) -> str | None:
        ident = asset.identifiers.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER
        ).first()
        return ident.value.upper() if ident else None

    def _event_defaults(self, raw: dict) -> dict:
        return {
            "record_date": raw.get("record_date"),
            "payment_date": raw.get("payment_date"),
            "declaration_date": raw.get("declaration_date"),
            "dividend": raw.get("dividend"),
            "adj_dividend": raw.get("adj_dividend"),
            "yield_value": raw.get("yield_value"),
            "frequency": raw.get("frequency"),
        }
