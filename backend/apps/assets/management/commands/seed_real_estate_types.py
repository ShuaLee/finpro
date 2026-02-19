from django.core.management.base import BaseCommand

from assets.models.real_estate.real_estate_type import RealEstateType


SYSTEM_REAL_ESTATE_TYPES = [
    ("Apartment", "Residential unit in a multi-unit building."),
    ("Condominium", "Individually owned unit within a shared building."),
    ("Single-Family Home", "Detached residential property."),
    ("Multi-Family Building", "Residential property with multiple units."),
    ("Office", "Commercial office property."),
    ("Retail", "Retail or shopping property."),
    ("Industrial", "Warehouse or industrial facility."),
    ("Mixed-Use", "Combination of residential and commercial uses."),
    ("Land", "Undeveloped or agricultural land."),
]


class Command(BaseCommand):
    help = "Populate system-defined real estate property types"

    def handle(self, *args, **options):
        created = 0
        skipped = 0

        for name, description in SYSTEM_REAL_ESTATE_TYPES:
            obj, was_created = RealEstateType.objects.get_or_create(
                name=name,
                created_by=None,
                defaults={"description": description},
            )

            if was_created:
                created += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"RealEstateTypes loaded: {created} created, {skipped} existing."
            )
        )
