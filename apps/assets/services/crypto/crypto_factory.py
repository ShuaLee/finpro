from django.db import transaction

from assets.models.crypto import CryptoAsset
from assets.services.base import BaseAssetFactory
from fx.models.fx import FXCurrency

from uuid import UUID


class CryptoAssetFactory(BaseAssetFactory):
    asset_type_slug = "cryptocurrency"

    @classmethod
    @transaction.atomic
    def create(
        cls,
        *,
        snapshot_id: UUID,
        base_symbol: str,
        pair_symbol: str,
        name: str | None,
        currency: FXCurrency,
        circulating_supply=None,
        total_supply=None,
        ico_date=None,
    ) -> CryptoAsset:
        asset = cls._create_asset()

        return CryptoAsset.objects.create(
            asset=asset,
            snapshot_id=snapshot_id,
            base_symbol=base_symbol,
            pair_symbol=pair_symbol,
            name=name,
            currency=currency,
            circulating_supply=circulating_supply,
            total_supply=total_supply,
            ico_date=ico_date,
        )
