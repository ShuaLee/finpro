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
        tracking_mode=None,
        price_source_mode=None,
    ):
        if account.position_mode == account.PositionMode.SYNCED and not account.allow_manual_overrides:
            raise ValidationError("Manual holding changes are disabled for this synced account.")

        allowed_types = account.allowed_asset_types.all()
        has_restrictions = allowed_types.exists()

        if asset:
            if account.enforce_restrictions and has_restrictions and asset.asset_type not in allowed_types:
                raise ValidationError(
                    f"Asset type '{asset.asset_type}' not allowed for this account."
                )

            if hasattr(asset, "custom") and asset.custom.owner != account.profile:
                raise ValidationError("You do not own this custom asset.")

            resolved_asset = asset
        else:
            if has_restrictions and allowed_types.count() == 1 and asset_type is None:
                resolved_type = allowed_types.first()
            else:
                if not asset_type:
                    raise ValidationError(
                        "Asset type must be specified for custom holdings."
                    )
                if account.enforce_restrictions and has_restrictions and not allowed_types.filter(pk=asset_type.pk).exists():
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
            tracking_mode=tracking_mode or Holding.TrackingMode.MANUAL,
            price_source_mode=price_source_mode or (
                Holding.PriceSourceMode.MANUAL
                if getattr(resolved_asset, "custom", None) is not None
                else Holding.PriceSourceMode.MARKET
            ),
        )
        _notify_holding_changed(holding)
        AccountAuditService.log(
            account=account,
            action="holding.created",
            metadata={"holding_id": holding.id},
        )
        return holding

    @staticmethod
    def update(
        *,
        holding,
        quantity=None,
        average_purchase_price=None,
        tracking_mode=None,
        price_source_mode=None,
    ):
        account = holding.account
        if account.position_mode == account.PositionMode.SYNCED and not account.allow_manual_overrides:
            raise ValidationError("Manual holding changes are disabled for this synced account.")

        if quantity is not None:
            holding.quantity = quantity
        if average_purchase_price is not None:
            holding.average_purchase_price = average_purchase_price
        if tracking_mode is not None:
            holding.tracking_mode = tracking_mode
        if price_source_mode is not None:
            holding.price_source_mode = price_source_mode

        holding.save()
        _notify_holding_changed(holding)
        AccountAuditService.log(
            account=holding.account,
            action="holding.updated",
            metadata={"holding_id": holding.id},
        )
        return holding
