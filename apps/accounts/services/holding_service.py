from django.core.exceptions import ValidationError
from django.db import transaction

from accounts.models import Holding
from assets.models.core import Asset
from assets.models.custom.custom_asset import CustomAsset
from schemas.services.scv_refresh_service import SCVRefreshService


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
        # 1️⃣ Resolve / create Asset
        # --------------------------------------------------
        if asset:
            resolved_asset = asset

        else:
            # ---- Custom asset path ----
            allowed = account.allowed_asset_types

            if not allowed.exists():
                raise ValidationError(
                    "Account does not allow any asset types."
                )

            if allowed.count() == 1:
                resolved_type = allowed.first()
            else:
                if not asset_type:
                    raise ValidationError(
                        "Asset type must be specified for custom holdings."
                    )
                if asset_type not in allowed:
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

            resolved_asset = Asset.objects.create(
                asset_type=resolved_type,
            )

            CustomAsset.objects.create(
                asset=resolved_asset,
                owner=account.profile,
                name=custom_name,
                currency=currency,
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
        SCVRefreshService.holding_changed(holding)

        return holding

    @staticmethod
    def update(*, holding, quantity=None, average_purchase_price=None):
        if quantity is not None:
            holding.quantity = quantity
        if average_purchase_price is not None:
            holding.average_purchase_price = average_purchase_price

        holding.save()

        # Sync SCVs after update
        account = holding.account
        if account.active_schema:
            SCVRefreshService.holding_changed(holding)

        return holding
