import pycountry

from django.db import transaction

from fx.models.country import Country
from external_data.providers.fmp.client import FMP_PROVIDER


class CountrySeederService:
    """
    Non-destructive Country reconciliation.
    """

    @transaction.atomic
    def run(self, *, deactivate_missing: bool = False):
        codes = FMP_PROVIDER.get_available_countries()

        created = updated = reactivated = 0
        seen: set[str] = set()

        for code in codes:
            code = code.strip().upper()
            if len(code) != 2:
                continue
            seen.add(code)

            iso = pycountry.countries.get(alpha_2=code)
            name = iso.name if iso else code

            obj, was_created = Country.objects.get_or_create(
                code=code,
                defaults={"name": name[:100], "is_active": True},
            )

            if was_created:
                created += 1
                continue

            changed_fields = []
            if obj.name != name:
                obj.name = name[:100]
                changed_fields.append("name")
            if not obj.is_active:
                obj.is_active = True
                changed_fields.append("is_active")
                reactivated += 1

            if changed_fields:
                obj.save(update_fields=changed_fields + ["updated_at"])
                updated += 1

        deactivated = 0
        if deactivate_missing and seen:
            deactivated = Country.objects.exclude(code__in=seen).filter(
                is_active=True
            ).update(is_active=False)

        return {
            "created": created,
            "updated": updated,
            "reactivated": reactivated,
            "deactivated": deactivated,
            "total": len(seen),
        }
