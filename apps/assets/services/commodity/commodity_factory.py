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
        symbol: str,
        name: str,
        currency: FXCurrency | None = None,
        trade_month: str | None = None,
    ) -> CommodityAsset:
        asset = cls._create_asset()

        return CommodityAsset.objects.create(
            asset=asset,
            symbol=symbol,
            name=name,
            currency=currency,
            trade_month=trade_month,
        )
