from django.core.exceptions import ValidationError
from django.db import transaction

from assets.models import RealEstateAsset, RealEstateType
from assets.services.real_estate.real_estate_factory import RealEstateAssetFactory
from fx.models.country import Country
from fx.models.fx import FXCurrency


class RealEstateTypeService:
    @staticmethod
    @transaction.atomic
    def create_custom(*, profile, name: str, description: str = "") -> RealEstateType:
        return RealEstateType.objects.create(
            name=name.strip(),
            description=description or "",
            created_by=profile,
        )

    @staticmethod
    @transaction.atomic
    def update_custom(*, real_estate_type: RealEstateType, name: str | None, description: str | None) -> RealEstateType:
        if real_estate_type.created_by_id is None:
            raise ValidationError("System property types cannot be modified.")

        if name is not None:
            real_estate_type.name = name.strip()
        if description is not None:
            real_estate_type.description = description
        real_estate_type.save()
        return real_estate_type

    @staticmethod
    @transaction.atomic
    def delete_custom(*, real_estate_type: RealEstateType):
        if real_estate_type.created_by_id is None:
            raise ValidationError("System property types cannot be deleted.")
        real_estate_type.delete()


class RealEstateAssetService:
    @staticmethod
    def _resolve_property_type(*, profile, property_type_id: int) -> RealEstateType:
        property_type = RealEstateType.objects.filter(id=property_type_id).first()
        if not property_type:
            raise ValidationError("Invalid property_type_id.")
        if property_type.created_by_id and property_type.created_by_id != profile.id:
            raise ValidationError("You cannot use another user's custom property type.")
        return property_type

    @staticmethod
    def _resolve_country(*, code: str) -> Country:
        country = Country.objects.filter(code=code.upper(), is_active=True).first()
        if not country:
            raise ValidationError("Invalid country code.")
        return country

    @staticmethod
    def _resolve_currency(*, code: str) -> FXCurrency:
        currency = FXCurrency.objects.filter(code=code.upper(), is_active=True).first()
        if not currency:
            raise ValidationError("Invalid currency code.")
        return currency

    @staticmethod
    @transaction.atomic
    def create(
        *,
        profile,
        property_type_id: int,
        country_code: str,
        currency_code: str,
        city: str = "",
        address: str = "",
        notes: str = "",
        is_owner_occupied: bool = False,
    ) -> RealEstateAsset:
        property_type = RealEstateAssetService._resolve_property_type(
            profile=profile,
            property_type_id=property_type_id,
        )
        country = RealEstateAssetService._resolve_country(code=country_code)
        currency = RealEstateAssetService._resolve_currency(code=currency_code)

        asset = RealEstateAssetFactory.create(
            owner=profile,
            property_type=property_type,
            country=country,
            currency=currency,
            city=city,
            address=address,
            notes=notes,
        )
        if is_owner_occupied != asset.is_owner_occupied:
            asset.is_owner_occupied = is_owner_occupied
            asset.save(update_fields=["is_owner_occupied"])
        return asset

    @staticmethod
    @transaction.atomic
    def update(
        *,
        real_estate_asset: RealEstateAsset,
        profile,
        property_type_id: int | None = None,
        country_code: str | None = None,
        currency_code: str | None = None,
        city: str | None = None,
        address: str | None = None,
        notes: str | None = None,
        is_owner_occupied: bool | None = None,
    ) -> RealEstateAsset:
        if property_type_id is not None:
            real_estate_asset.property_type = RealEstateAssetService._resolve_property_type(
                profile=profile,
                property_type_id=property_type_id,
            )
        if country_code is not None:
            real_estate_asset.country = RealEstateAssetService._resolve_country(code=country_code)
        if currency_code is not None:
            real_estate_asset.currency = RealEstateAssetService._resolve_currency(code=currency_code)
        if city is not None:
            real_estate_asset.city = city
        if address is not None:
            real_estate_asset.address = address
        if notes is not None:
            real_estate_asset.notes = notes
        if is_owner_occupied is not None:
            real_estate_asset.is_owner_occupied = is_owner_occupied

        real_estate_asset.save()
        return real_estate_asset

    @staticmethod
    @transaction.atomic
    def delete(*, real_estate_asset: RealEstateAsset):
        real_estate_asset.delete()

