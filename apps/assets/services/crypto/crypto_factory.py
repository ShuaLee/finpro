# assets/services/factories/crypto.py
from django.db import transaction

from assets.models.crypto import CryptoAsset
from assets.services.base import BaseAssetFactory
from fx.models.fx import FXCurrency


class CryptoAssetFactory(BaseAssetFactory):
    asset_type_slug = "crypto"

    @classmethod
    @transaction.atomic
    def create(
        cls,
        *,
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
            base_symbol=base_symbol,
            pair_symbol=pair_symbol,
            name=name,
            currency=currency,
            circulating_supply=circulating_supply,
            total_supply=total_supply,
            ico_date=ico_date,
        )
