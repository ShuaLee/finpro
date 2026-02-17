from django.db import transaction

from fx.models.fx import FXCurrency
from external_data.providers.fmp.fx.fetchers import fetch_fx_universe
from external_data.providers.fmp.client import FMP_PROVIDER


class FXCurrencySeederService:
    """
    Non-destructive FX currency reconciliation.
    """

    @transaction.atomic
    def run(self, *, deactivate_missing: bool = False):
        rows = FMP_PROVIDER.request(fetch_fx_universe)

        seen: dict[str, str | None] = {}

        for row in rows:
            for code_key, name_key in (
                ("fromCurrency", "fromName"),
                ("toCurrency", "toName"),
            ):
                code = row.get(code_key)
                name = row.get(name_key)

                if not code:
                    continue

                code = code.strip().upper()
                name = name.strip() if isinstance(name, str) else None

                seen.setdefault(code, name)

        created = updated = reactivated = 0

        for code, name in seen.items():
            obj, was_created = FXCurrency.objects.get_or_create(
                code=code,
                defaults={
                    "name": name[:150] if name else code,
                    "is_active": True,
                },
            )

            if was_created:
                created += 1
                continue

            changed_fields = []
            next_name = name[:150] if name else code
            if obj.name != next_name:
                obj.name = next_name
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
            deactivated = FXCurrency.objects.exclude(code__in=seen.keys()).filter(
                is_active=True
            ).update(is_active=False)

        return {
            "created": created,
            "updated": updated,
            "reactivated": reactivated,
            "deactivated": deactivated,
            "total": len(seen),
        }
