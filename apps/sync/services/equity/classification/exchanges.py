import logging

from django.db import transaction

from assets.models.exchanges import Exchange
from fx.models.country import Country
from external_data.providers.fmp.client import FMP_PROVIDER
from sync.services.base import BaseSyncService

logger = logging.getLogger(__name__)


class ExchangeReferenceSyncService(BaseSyncService):
    """
    Sync exchanges from the provider.

    Behavior:
    - Create missing exchanges
    - Update mutable exchange metadata
    - NEVER delete exchanges
    - NEVER overwrite user-owned exchanges
    """

    name = "equity.reference.exchanges"

    @transaction.atomic
    def _sync(self) -> dict:
        provider = FMP_PROVIDER

        exchanges = provider.get_available_exchanges()

        created = 0
        updated = 0

        for rec in exchanges:
            code = (rec.get("exchange") or "").strip()
            name = (rec.get("name") or "").strip()
            country_code = (rec.get("countryCode") or "").strip()

            if not code or not name:
                continue

            slug = code.lower()

            country = None
            if country_code:
                country = Country.objects.filter(
                    code__iexact=country_code
                ).first()

            obj, was_created = Exchange.objects.update_or_create(
                slug=slug,
                owner=None,  # system-level only
                defaults={
                    "code": code,
                    "name": name,
                    "country": country,
                    "symbol_suffix": rec.get("symbolSuffix"),
                    "delay": rec.get("delay"),
                    "is_system": True,
                },
            )

            if was_created:
                created += 1
            else:
                updated += 1

        logger.info(
            "[EXCHANGE_SYNC] created=%s updated=%s",
            created,
            updated,
        )

        return {
            "success": True,
            "created": created,
            "updated": updated,
        }
