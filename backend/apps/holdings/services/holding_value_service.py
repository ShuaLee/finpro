from decimal import Decimal

from django.core.exceptions import ValidationError

from apps.holdings.models import Holding, HoldingFactDefinition, HoldingFactValue, HoldingOverride, Portfolio
from apps.holdings.services.value_utils import parse_typed_value, serialize_typed_value


class HoldingValueService:
    @staticmethod
    def create_fact_definition(
        *,
        portfolio: Portfolio,
        key: str,
        label: str,
        data_type: str,
        description: str = "",
        is_active: bool = True,
    ) -> HoldingFactDefinition:
        definition = HoldingFactDefinition(
            portfolio=portfolio,
            key=key,
            label=label,
            data_type=data_type,
            description=description,
            is_active=is_active,
        )
        definition.save()
        return definition

    @staticmethod
    def update_fact_definition(
        *,
        definition: HoldingFactDefinition,
        profile,
        label: str | None = None,
        description: str | None = None,
        data_type: str | None = None,
        is_active: bool | None = None,
    ) -> HoldingFactDefinition:
        if definition.portfolio.profile != profile:
            raise ValidationError("You cannot edit another user's fact definition.")
        if label is not None:
            definition.label = label
        if description is not None:
            definition.description = description
        if data_type is not None:
            definition.data_type = data_type
        if is_active is not None:
            definition.is_active = is_active
        definition.save()
        return definition

    @staticmethod
    def upsert_fact_value(*, holding: Holding, definition: HoldingFactDefinition, value):
        serialized = serialize_typed_value(data_type=definition.data_type, value=value)
        fact_value, _ = HoldingFactValue.objects.update_or_create(
            holding=holding,
            definition=definition,
            defaults={"value": serialized},
        )
        return fact_value

    @staticmethod
    def upsert_override(*, holding: Holding, key: str, data_type: str, value):
        serialized = serialize_typed_value(data_type=data_type, value=value)
        override, _ = HoldingOverride.objects.update_or_create(
            holding=holding,
            key=key.strip().lower(),
            defaults={"data_type": data_type, "value": serialized},
        )
        return override

    @staticmethod
    def get_override_value(*, holding: Holding, key: str):
        override = next(
            (item for item in getattr(holding, "_prefetched_objects_cache", {}).get("overrides", []) if item.key == key),
            None,
        )
        if override is None:
            override = getattr(holding, "overrides", HoldingOverride.objects.none()).filter(key=key).first()
        if override is None:
            return None
        return parse_typed_value(data_type=override.data_type, raw_value=override.value)

    @staticmethod
    def get_builtin_value(*, holding: Holding, key: str):
        asset = holding.asset
        asset_data = asset.data or {}
        market_data = getattr(asset, "market_data", None)

        if key == "asset_name":
            return asset.name
        if key == "asset_symbol":
            return asset.symbol
        if key == "asset_type":
            return asset.asset_type.slug
        if key == "quantity":
            return holding.quantity
        if key == "unit_value":
            return holding.unit_value
        if key == "unit_cost_basis":
            return holding.unit_cost_basis
        if key == "price":
            if holding.unit_value is not None:
                return holding.unit_value
            return asset.current_price
        if key == "current_value":
            price = HoldingValueService.get_builtin_value(holding=holding, key="price")
            if price is None:
                return None
            return Decimal(str(holding.quantity)) * Decimal(str(price))
        if key == "invested_value":
            if holding.unit_cost_basis is None:
                return None
            return Decimal(str(holding.quantity)) * Decimal(str(holding.unit_cost_basis))
        if key == "sector":
            return asset_data.get("custom_sector") or asset_data.get("sector")
        if key == "industry":
            return asset_data.get("industry")
        if key == "country":
            return asset_data.get("country")
        if key == "exchange":
            return asset_data.get("exchange") or getattr(market_data, "last_seen_exchange", None)
        if key == "currency":
            return asset_data.get("currency")
        if key == "is_public":
            return asset.owner_id is None
        return None

    @staticmethod
    def get_effective_value(*, holding: Holding, key: str):
        if key != "price":
            override_value = HoldingValueService.get_override_value(holding=holding, key=key)
            if override_value is not None:
                return override_value

        builtin_value = HoldingValueService.get_builtin_value(holding=holding, key=key)
        if builtin_value is not None:
            return builtin_value

        definition = next(
            (
                item for item in getattr(holding, "_prefetched_objects_cache", {}).get("fact_values", [])
                if item.definition.key == key
            ),
            None,
        )
        if definition is None:
            definition = (
                getattr(holding, "fact_values", HoldingFactValue.objects.none())
                .select_related("definition")
                .filter(definition__key=key)
                .first()
            )
        if definition is None:
            return None
        return parse_typed_value(data_type=definition.definition.data_type, raw_value=definition.value)

    @staticmethod
    def get_effective_summary(*, holding: Holding) -> dict:
        return {
            "price": HoldingValueService.get_effective_value(holding=holding, key="price"),
            "current_value": HoldingValueService.get_effective_value(holding=holding, key="current_value"),
            "sector": HoldingValueService.get_effective_value(holding=holding, key="sector"),
            "industry": HoldingValueService.get_effective_value(holding=holding, key="industry"),
            "country": HoldingValueService.get_effective_value(holding=holding, key="country"),
            "exchange": HoldingValueService.get_effective_value(holding=holding, key="exchange"),
        }
