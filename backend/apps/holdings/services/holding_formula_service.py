from decimal import Decimal

from apps.holdings.services.holding_value_service import HoldingValueService
from apps.integrations.services import FXRateService


class HoldingFormulaService:
    SYSTEM_IDENTIFIERS = {
        "fx_rate",
        "market_value",
        "current_value",
        "cost_basis",
        "unrealized_gain",
        "unrealized_gain_pct",
    }

    @staticmethod
    def _asset_currency(*, holding) -> str:
        return (HoldingValueService.get_effective_value(holding=holding, key="currency") or "").strip().upper()

    @staticmethod
    def _profile_currency(*, holding) -> str:
        profile = holding.container.portfolio.profile
        return (getattr(profile, "currency", "") or "").strip().upper()

    @staticmethod
    def _to_decimal(value) -> Decimal | None:
        if value is None:
            return None
        return Decimal(str(value))

    @staticmethod
    def evaluate(*, holding, identifier: str):
        normalized = (identifier or "").strip().lower()

        if normalized == "fx_rate":
            asset_currency = HoldingFormulaService._asset_currency(holding=holding)
            profile_currency = HoldingFormulaService._profile_currency(holding=holding)
            return FXRateService.get_rate(
                base_currency=asset_currency or profile_currency,
                quote_currency=profile_currency or asset_currency,
            )

        if normalized == "market_value":
            quantity = HoldingFormulaService._to_decimal(
                HoldingValueService.get_effective_value(holding=holding, key="quantity")
            )
            price = HoldingFormulaService._to_decimal(
                HoldingValueService.get_effective_value(holding=holding, key="price")
            )
            if quantity is None or price is None:
                return None
            return quantity * price

        if normalized == "current_value":
            market_value = HoldingFormulaService.evaluate(holding=holding, identifier="market_value")
            if market_value is None:
                return None
            fx_rate = HoldingFormulaService.evaluate(holding=holding, identifier="fx_rate")
            return market_value * fx_rate

        if normalized == "cost_basis":
            quantity = HoldingFormulaService._to_decimal(
                HoldingValueService.get_effective_value(holding=holding, key="quantity")
            )
            unit_cost_basis = HoldingFormulaService._to_decimal(
                HoldingValueService.get_effective_value(holding=holding, key="unit_cost_basis")
            )
            if quantity is None or unit_cost_basis is None:
                return None
            fx_rate = HoldingFormulaService.evaluate(holding=holding, identifier="fx_rate")
            return quantity * unit_cost_basis * fx_rate

        if normalized == "unrealized_gain":
            current_value = HoldingFormulaService.evaluate(holding=holding, identifier="current_value")
            cost_basis = HoldingFormulaService.evaluate(holding=holding, identifier="cost_basis")
            if current_value is None or cost_basis is None:
                return None
            return current_value - cost_basis

        if normalized == "unrealized_gain_pct":
            unrealized_gain = HoldingFormulaService.evaluate(holding=holding, identifier="unrealized_gain")
            cost_basis = HoldingFormulaService.evaluate(holding=holding, identifier="cost_basis")
            if unrealized_gain is None or cost_basis in (None, Decimal("0")):
                return None
            return unrealized_gain / cost_basis

        return HoldingValueService.get_effective_value(holding=holding, key=normalized)

    @staticmethod
    def evaluate_many(*, holding, identifiers: list[str] | tuple[str, ...]):
        return {
            identifier: HoldingFormulaService.evaluate(holding=holding, identifier=identifier)
            for identifier in identifiers
        }

    @staticmethod
    def summary(*, holding) -> dict:
        return HoldingFormulaService.evaluate_many(
            holding=holding,
            identifiers=[
                "fx_rate",
                "market_value",
                "current_value",
                "cost_basis",
                "unrealized_gain",
                "unrealized_gain_pct",
            ],
        )
