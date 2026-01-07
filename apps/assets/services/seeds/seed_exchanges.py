import logging

from django.db import models, transaction

from assets.models.exchanges import Exchange
from fx.models.country import Country

from external_data.providers.fmp.classifications.fetchers import fetch_available_exchanges

logger = logging.getLogger(__name__)


@transaction.atomic
def seed_exchanges() -> int:
    """
    Seed FMP exchanges into the Exchange table as system-level entries.
    Does not overwrite user-created exchanges.
    """

    logger.info("Seeding exchanges from FMP...")

    data = fetch_available_exchanges()

    if not data:
        logger.warning("No exchanges returned from FMP.")
        return 0

    created = 0

    for rec in data:
        code = (rec.get("exchange") or "").strip()
        name = (rec.get("name") or "").strip()
        country_code = (rec.get("countryCode") or "").strip()
        symbol_suffix = rec.get("symbolSuffix") or None
        delay = rec.get("delay") or None

        if not code or not name:
            continue

        # Resolve FK
        country = None
        if country_code:
            country = Country.objects.filter(code__iexact=country_code).first()

        slug = code.lower()

        obj, created_flag = Exchange.objects.update_or_create(
            slug=slug,
            owner=None,  # system-level only
            defaults={
                "code": code,
                "name": name,
                "country": country,
                "symbol_suffix": symbol_suffix,
                "delay": delay,
                "is_system": True,
            }
        )

        if created_flag:
            created += 1

    logger.info(f"Seeded {created} exchanges.")
    return created
