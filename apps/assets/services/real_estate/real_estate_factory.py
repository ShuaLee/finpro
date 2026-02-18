from django.db import transaction

from assets.models.real_estate import RealEstateAsset, RealEstateType
from assets.services.base import BaseAssetFactory
from fx.models.fx import FXCurrency
from fx.models.country import Country
from profiles.models import Profile


class RealEstateAssetFactory(BaseAssetFactory):
    asset_type_slug = "real_estate"

    @classmethod
    @transaction.atomic
    def create(
        cls,
        *,
        owner: Profile,
        property_type: RealEstateType,
        country: Country,
        currency: FXCurrency,
        city: str = "",
        address: str = "",
        notes: str = "",
    ) -> RealEstateAsset:
        asset = cls._create_asset()

        return RealEstateAsset.objects.create(
            asset=asset,
            owner=owner,
            property_type=property_type,
            country=country,
            currency=currency,
            city=city,
            address=address,
            notes=notes,
        )
