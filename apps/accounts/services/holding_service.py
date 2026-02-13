from django.core.exceptions import ValidationError
from django.db import transaction

from accounts.models import Holding
from assets.models.core import Asset
from assets.models.custom.custom_asset import CustomAsset
from schemas.services.orchestration import SchemaOrchestrationService


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
        # --------------------------------------------------
        # 1️⃣ Resolve / validate Asset
        # --------------------------------------------------
        allowed_types = account.allowed_asset_types

        if not allowed_types.exists():
            raise ValidationError(
                "Account does not allow any asset types."
            )

        # ----------------------------------------------
        # Existing asset path
        # ----------------------------------------------
        if asset:
            # AssetType must be allowed
            if asset.asset_type not in allowed_types:
                raise ValidationError(
                    f"Asset type '{asset.asset_type}' not allowed for this account."
                )

            # Custom asset ownership check
            if hasattr(asset, "custom"):
                if asset.custom.owner != account.profile:
                    raise ValidationError(
                        "You do not own this custom asset."
                    )

            resolved_asset = asset

        # ----------------------------------------------
        # Custom asset creation path
        # ----------------------------------------------
        else:
            # Resolve asset type
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
                raise ValidationError(
                    "Custom asset name is required."
                )

            if not currency:
                raise ValidationError(
                    "Currency is required for custom assets."
                )

            # Create Asset
            resolved_asset = Asset.objects.create(
                asset_type=resolved_type,
            )

            # Create CustomAsset extension
            CustomAsset.objects.create(
                asset=resolved_asset,
                owner=account.profile,
                name=custom_name,
                currency=currency,
                reason=CustomAsset.Reason.USER,
            )

        # --------------------------------------------------
        # 2️⃣ Create Holding
        # --------------------------------------------------
        holding = Holding.objects.create(
            account=account,
            asset=resolved_asset,
            quantity=quantity,
            average_purchase_price=average_purchase_price,
        )

        # --------------------------------------------------
        # 3️⃣ Trigger schema recompute
        # --------------------------------------------------
        if account.active_schema:
            SchemaOrchestrationService.holding_changed(holding)

        return holding

    @staticmethod
    def update(*, holding, quantity=None, average_purchase_price=None):
        if quantity is not None:
            holding.quantity = quantity
        if average_purchase_price is not None:
            holding.average_purchase_price = average_purchase_price

        holding.save()

        if holding.account.active_schema:
            SchemaOrchestrationService.holding_changed(holding)

        return holding
