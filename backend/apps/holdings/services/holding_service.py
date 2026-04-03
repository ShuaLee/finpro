from decimal import Decimal

from django.core.exceptions import ValidationError

from apps.assets.models import Asset
from apps.holdings.models import Container, Holding


class HoldingService:
    @staticmethod
    def create_holding(
        *,
        container: Container,
        asset: Asset,
        quantity: Decimal | None = None,
        unit_value: Decimal | None = None,
        unit_cost_basis: Decimal | None = None,
        notes: str = "",
        data: dict | None = None,
    ) -> Holding:
        holding = Holding(
            container=container,
            asset=asset,
            quantity=quantity if quantity is not None else Decimal("1"),
            unit_value=unit_value,
            unit_cost_basis=unit_cost_basis,
            notes=(notes or "").strip(),
            data=data or {},
        )
        holding.save()
        return holding

    @staticmethod
    def update_holding(
        *,
        holding: Holding,
        profile,
        quantity: Decimal | None = None,
        unit_value: Decimal | None = None,
        unit_cost_basis: Decimal | None = None,
        notes: str | None = None,
        data: dict | None = None,
    ) -> Holding:
        if holding.container.portfolio.profile != profile:
            raise ValidationError("You cannot edit another user's holding.")

        if quantity is not None:
            holding.quantity = quantity
        if unit_value is not None:
            holding.unit_value = unit_value
        if unit_cost_basis is not None:
            holding.unit_cost_basis = unit_cost_basis
        if notes is not None:
            holding.notes = notes
        if data is not None:
            holding.data = data

        holding.save()
        return holding

    @staticmethod
    def upsert_holding(
        *,
        container: Container,
        asset: Asset,
        quantity: Decimal | None = None,
        unit_value: Decimal | None = None,
        unit_cost_basis: Decimal | None = None,
        notes: str = "",
        data: dict | None = None,
    ) -> Holding:
        holding = Holding.objects.filter(container=container, asset=asset).first()
        if holding is None:
            return HoldingService.create_holding(
                container=container,
                asset=asset,
                quantity=quantity,
                unit_value=unit_value,
                unit_cost_basis=unit_cost_basis,
                notes=notes,
                data=data,
            )

        if quantity is not None:
            holding.quantity = quantity
        if unit_value is not None:
            holding.unit_value = unit_value
        if unit_cost_basis is not None:
            holding.unit_cost_basis = unit_cost_basis
        holding.notes = (notes or "").strip()
        holding.data = data or holding.data
        holding.save()
        return holding
