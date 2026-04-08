from django.core.exceptions import ValidationError
from django.db import transaction

from apps.integrations.services import MarketDataService
from apps.users.models import SupportedCountry, SupportedCurrency


class ReferenceDataService:
    @staticmethod
    def normalize_country_code(code: str | None) -> str:
        return (code or "").strip().upper()

    @staticmethod
    def normalize_currency_code(code: str | None) -> str:
        return (code or "").strip().upper()

    @staticmethod
    def validate_country_code(code: str | None) -> str:
        normalized = ReferenceDataService.normalize_country_code(code)
        if not normalized:
            return ""
        if not SupportedCountry.objects.filter(is_active=True).exists():
            return normalized
        if not SupportedCountry.objects.filter(code=normalized, is_active=True).exists():
            raise ValidationError(f"Unsupported country code: '{normalized}'")
        return normalized

    @staticmethod
    def validate_currency_code(code: str | None) -> str:
        normalized = ReferenceDataService.normalize_currency_code(code)
        if not normalized:
            raise ValidationError("Currency is required.")
        if not SupportedCurrency.objects.filter(is_active=True).exists():
            return normalized
        if not SupportedCurrency.objects.filter(code=normalized, is_active=True).exists():
            raise ValidationError(f"Unsupported currency code: '{normalized}'")
        return normalized

    @staticmethod
    @transaction.atomic
    def sync_supported_countries(*, deactivate_missing: bool = False) -> dict:
        codes = MarketDataService.get_available_countries()
        seen: set[str] = set()
        created = updated = reactivated = 0

        for raw_code in codes:
            code = ReferenceDataService.normalize_country_code(raw_code)
            if len(code) != 2:
                continue
            seen.add(code)

            obj, was_created = SupportedCountry.objects.get_or_create(
                code=code,
                defaults={"name": code, "is_active": True},
            )
            if was_created:
                created += 1
                continue

            changed_fields: list[str] = []
            if obj.name != code:
                obj.name = code
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
            deactivated = SupportedCountry.objects.exclude(code__in=seen).filter(is_active=True).update(
                is_active=False
            )

        return {
            "created": created,
            "updated": updated,
            "reactivated": reactivated,
            "deactivated": deactivated,
            "total": len(seen),
        }

    @staticmethod
    @transaction.atomic
    def sync_supported_currencies(*, deactivate_missing: bool = False) -> dict:
        rows = MarketDataService.get_forex_list()
        seen: dict[str, str] = {}

        for row in rows:
            for code_key, name_key in (("fromCurrency", "fromName"), ("toCurrency", "toName")):
                code = ReferenceDataService.normalize_currency_code(row.get(code_key))
                if not code:
                    continue
                name = (row.get(name_key) or code).strip()
                seen.setdefault(code, name)

        created = updated = reactivated = 0
        for code, name in seen.items():
            obj, was_created = SupportedCurrency.objects.get_or_create(
                code=code,
                defaults={"name": name[:150], "is_active": True},
            )
            if was_created:
                created += 1
                continue

            changed_fields: list[str] = []
            next_name = name[:150]
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
            deactivated = SupportedCurrency.objects.exclude(code__in=seen.keys()).filter(is_active=True).update(
                is_active=False
            )

        return {
            "created": created,
            "updated": updated,
            "reactivated": reactivated,
            "deactivated": deactivated,
            "total": len(seen),
        }
