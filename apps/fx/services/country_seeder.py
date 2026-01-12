import pycountry

from django.db import transaction

from fx.models.country import Country
from external_data.providers.fmp.client import FMP_PROVIDER


class CountrySeederService:
    """
    Seeds Country using:
    - FMP as source of truth for WHICH countries exist
    - ISO-3166 (pycountry) as source of truth for NAMES
    """

    @transaction.atomic
    def run(self):
        codes = FMP_PROVIDER.get_available_countries()

        created = 0
        existing = 0
        skipped = 0

        for code in codes:
            code = code.strip().upper()

            if not code or len(code) != 2:
                skipped += 1
                continue

            iso = pycountry.countries.get(alpha_2=code)
            name = iso.name if iso else code  # safe fallback

            _, was_created = Country.objects.get_or_create(
                code=code,
                defaults={"name": name[:100]},
            )

            if was_created:
                created += 1
            else:
                existing += 1

        return {
            "created": created,
            "existing": existing,
            "skipped": skipped,
            "total": len(codes),
        }
