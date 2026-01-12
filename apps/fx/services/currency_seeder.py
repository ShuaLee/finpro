from django.db import transaction

from fx.models.fx import FXCurrency
from external_data.providers.fmp.fx.fetchers import fetch_fx_universe


class FXCurrencySeederService:
    """
    Seeds FXCurrency strictly from FMP forex-list.

    Rules:
    - Currency existence is defined ONLY by FMP
    - Code is canonical
    - Name is best-effort metadata
    - Name is REQUIRED (fallback = code)
    - Never overwrite existing rows
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

                # Keep first-seen name only
                seen.setdefault(code, name)

        created = 0
        existing = 0

        for code, name in seen.items():
            _, was_created = FXCurrency.objects.get_or_create(
                code=code,
                defaults={
                    # 🔑 CRITICAL FIX
                    "name": (name or code)[:150],
                },
            )

            if was_created:
                created += 1
            else:
                existing += 1

        return {
            "created": created,
            "existing": existing,
            "total": len(seen),
        }
