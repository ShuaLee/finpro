from django.db import transaction

from assets.models.real_estate import RealEstateAsset, RealEstateType
from assets.services.base import BaseAssetFactory
from fx.models.fx import FXCurrency
from fx.models.country import Country
from users.models.profile import Profile


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
        estimated_value,
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
            estimated_value=estimated_value,
            currency=currency,
            city=city,
            address=address,
            notes=notes,
        )
