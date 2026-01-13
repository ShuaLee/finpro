from django.db import transaction

from fx.models.fx import FXCurrency
from external_data.providers.fmp.fx.fetchers import fetch_fx_universe


class FXCurrencySeederService:
    """
    Non-destructive FX currency reconciliation.
    """

    @transaction.atomic
    def run(self):
        rows = fetch_fx_universe()

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

        created = updated = 0

        for code, name in seen.items():
            obj, was_created = FXCurrency.objects.get_or_create(
                code=code,
                defaults={"name": name[:150] if name else code},
            )

            if was_created:
                created += 1
            elif not obj.name and name:
                obj.name = name[:150]
                obj.save(update_fields=["name"])
                updated += 1

        return {
            "created": created,
            "updated": updated,
            "total": len(seen),
        }
