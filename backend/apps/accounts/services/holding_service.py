from django.core.exceptions import ValidationError
from django.db import transaction

from accounts.models import Holding
from assets.models.core import Asset
from assets.models.custom.custom_asset import CustomAsset

from .audit_service import AccountAuditService

def _notify_holding_changed(holding):
    try:
        from schemas.services.orchestration import SchemaOrchestrationService
    except Exception:
        return
    SchemaOrchestrationService.holding_changed(holding)


class HoldingService:
    @staticmethod
    @transaction.atomic
    def create(
        *,
        account,
        quantity,
        asset=None,
        asset_type=None,
        custom_name=None,
        currency=None,
        average_purchase_price=None,
    ):
        if account.position_mode == account.PositionMode.SYNCED and not account.allow_manual_overrides:
            raise ValidationError("Manual holding changes are disabled for this synced account.")

        allowed_types = account.allowed_asset_types

        if not allowed_types.exists():
            raise ValidationError("Account does not allow any asset types.")

        if asset:
            if asset.asset_type not in allowed_types:
                raise ValidationError(
                    f"Asset type '{asset.asset_type}' not allowed for this account."
                )

            if hasattr(asset, "custom") and asset.custom.owner != account.profile:
                raise ValidationError("You do not own this custom asset.")

            resolved_asset = asset
        else:
            if allowed_types.count() == 1:
                resolved_type = allowed_types.first()
            else:
                if not asset_type:
                    raise ValidationError(
                        "Asset type must be specified for custom holdings."
                    )
                if not allowed_types.filter(pk=asset_type.pk).exists():
                    raise ValidationError(
                        f"Asset type '{asset_type}' not allowed for this account."
                    )
                resolved_type = asset_type

            if not custom_name:
                raise ValidationError("Custom asset name is required.")
            if not currency:
                raise ValidationError("Currency is required for custom assets.")

            resolved_asset = Asset.objects.create(asset_type=resolved_type)
            CustomAsset.objects.create(
                asset=resolved_asset,
                owner=account.profile,
                name=custom_name,
                currency=currency,
                reason=CustomAsset.Reason.USER,
            )

        holding = Holding.objects.create(
            account=account,
            asset=resolved_asset,
            quantity=quantity,
            average_purchase_price=average_purchase_price,
        )
        _notify_holding_changed(holding)
        AccountAuditService.log(
            account=account,
            action="holding.created",
            metadata={"holding_id": holding.id},
        )
        return holding

    @staticmethod
    def update(*, holding, quantity=None, average_purchase_price=None):
        account = holding.account
        if account.position_mode == account.PositionMode.SYNCED and not account.allow_manual_overrides:
            raise ValidationError("Manual holding changes are disabled for this synced account.")

        if quantity is not None:
            holding.quantity = quantity
        if average_purchase_price is not None:
            holding.average_purchase_price = average_purchase_price

        holding.save()
        _notify_holding_changed(holding)
        AccountAuditService.log(
            account=holding.account,
            action="holding.updated",
            metadata={"holding_id": holding.id},
        )
        return holding
