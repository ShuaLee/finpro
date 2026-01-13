import pycountry

from django.db import transaction

from fx.models.country import Country
from external_data.providers.fmp.client import FMP_PROVIDER


class CountrySeederService:
    """
    Non-destructive Country reconciliation.
    """

    @transaction.atomic
    def run(self):
        codes = FMP_PROVIDER.get_available_countries()

        created = updated = 0

        for code in codes:
            code = code.strip().upper()
            if len(code) != 2:
                continue

            iso = pycountry.countries.get(alpha_2=code)
            name = iso.name if iso else code

            obj, was_created = Country.objects.get_or_create(
                code=code,
                defaults={"name": name[:100]},
            )

            if was_created:
                created += 1
            elif obj.name != name:
                obj.name = name[:100]
                obj.save(update_fields=["name"])
                updated += 1

        return {
            "created": created,
            "updated": updated,
            "total": len(codes),
        }
