from uuid import UUID
from django.db import transaction

from assets.models.commodity import CommodityAsset
from assets.services.base import BaseAssetFactory
from fx.models.fx import FXCurrency


class CommodityAssetFactory(BaseAssetFactory):
    asset_type_slug = "commodity"

    @classmethod
    @transaction.atomic
    def create(
        cls,
        *,
        snapshot_id: UUID,
        symbol: str,
        name: str | None,
        currency: FXCurrency,
        exchange: str | None = None,
        trade_month: str | None = None,
    ) -> CommodityAsset:
        asset = cls._create_asset()

        return CommodityAsset.objects.create(
            asset=asset,
            snapshot_id=snapshot_id,
            symbol=symbol,
            name=name,
            currency=currency,
            exchange=exchange,
            trade_month=trade_month,
        )
