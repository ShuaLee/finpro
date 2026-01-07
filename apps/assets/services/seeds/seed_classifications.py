import logging
from django.db import transaction

from assets.models.classifications.sector import Sector
from assets.models.classifications.industry import Industry

from external_data.providers.fmp.classifications.fetchers import (
    fetch_available_sectors,
    fetch_available_industries,
)

logger = logging.getLogger(__name__)


class ClassificationSeeder:

    # ---------------------------------------------------------
    # Seed Sectors
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def seed_sectors() -> dict:
        data = fetch_available_sectors() or []
        created = updated = 0

        for name in data:   # name is already a string
            name = name.strip()
            if not name:
                continue

            obj, was_created = Sector.objects.update_or_create(
                name=name,
                defaults={
                    "is_system": True,
                    "owner": None,
                }
            )

            if was_created:
                created += 1
            else:
                updated += 1

        return {"created": created, "updated": updated}

    # ---------------------------------------------------------
    # Seed Industries
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def seed_industries() -> dict:
        data = fetch_available_industries() or []
        created = updated = 0

        for name in data:   # name is already a string
            name = name.strip()
            if not name:
                continue

            obj, was_created = Industry.objects.update_or_create(
                name=name,
                defaults={
                    "is_system": True,
                    "owner": None,
                }
            )

            if was_created:
                created += 1
            else:
                updated += 1

        return {"created": created, "updated": updated}

    # ---------------------------------------------------------
    # Seed All
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def seed_all() -> dict:
        logger.info("🏷  Seeding Sectors & Industries from FMP...")

        sectors = ClassificationSeeder.seed_sectors()
        industries = ClassificationSeeder.seed_industries()

        logger.info(
            f"Sectors: {sectors['created']} created / {sectors['updated']} updated — "
            f"Industries: {industries['created']} created / {industries['updated']} updated"
        )

        return {
            "sectors": sectors,
            "industries": industries,
        }
