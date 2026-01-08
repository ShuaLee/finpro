import logging
from django.db import transaction

from assets.models.classifications import Exchange, Sector, Industry
from external_data.providers.fmp.client import FMP_PROVIDER
from fx.models.country import Country


logger = logging.getLogger(__name__)


class ClassificationSeeder:
    """
    Bootstrap seeder for market reference data.

    Behavior:
    - Create missing records
    - Update mutable exchange metadata
    - NEVER delete records
    """

    # ---------------------------------------------------------
    # Sectors
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def seed_sectors() -> dict:
        data = FMP_PROVIDER.get_available_sectors()
        created = unchanged = 0

        for name in data:
            name = (name or "").strip()
            if not name:
                continue

            _, was_created = Sector.objects.update_or_create(
                name=name,
            )

            if was_created:
                created += 1
            else:
                unchanged += 1

        return {"created": created, "unchanged": unchanged}

    # ---------------------------------------------------------
    # Industries
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def seed_industries() -> dict:
        data = FMP_PROVIDER.get_available_industries()
        created = unchanged = 0

        for name in data:
            name = (name or "").strip()
            if not name:
                continue

            _, was_created = Industry.objects.update_or_create(
                name=name,
            )

            if was_created:
                created += 1
            else:
                unchanged += 1

        return {"created": created, "unchanged": unchanged}

    # ---------------------------------------------------------
    # Exchanges
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def seed_exchanges() -> dict:
        data = FMP_PROVIDER.get_available_exchanges()
        created = unchanged = 0

        for rec in data:
            code = (rec.get("code") or "").strip()
            name = (rec.get("name") or "").strip()
            country_code = (rec.get("country_code") or "").strip()

            if not code or not name:
                continue

            country = None
            if country_code:
                country = Country.objects.filter(
                    code__iexact=country_code
                ).first()

            slug = code.lower()

            _, was_created = Exchange.objects.update_or_create(
                slug=slug,
                owner=None,
                defaults={
                    "code": code,
                    "name": name,
                    "country": country,
                    "symbol_suffix": rec.get("symbol_suffix"),
                    "delay": rec.get("delay"),
                    "is_system": True,
                },
            )

            if was_created:
                created += 1
            else:
                unchanged += 1

            return {"created": created, "unchanged": unchanged}

    # ---------------------------------------------------------
    # All
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def seed_all() -> dict:
        logger.info("🏷  Seeding market classifications from provider...")

        return {
            "sectors": ClassificationSeeder.seed_sectors(),
            "industries": ClassificationSeeder.seed_industries(),
            "exchanges": ClassificationSeeder.seed_exchanges(),
        }
