from django.core.exceptions import ValidationError
from django.db import transaction

from assets.models import Asset, AssetType, CustomAsset
from assets.services.policy import AssetPolicyService
from fx.models.fx import FXCurrency


class CustomAssetService:
    @staticmethod
    def _get_asset_type_for_profile(*, profile, slug: str) -> AssetType:
        asset_type = AssetType.objects.filter(slug=slug).first()
        if not asset_type:
            raise ValidationError("Invalid asset_type_slug.")
        AssetPolicyService.assert_asset_type_usable_by_profile(
            profile=profile,
            asset_type=asset_type,
        )
        return asset_type

    @staticmethod
    def _get_currency(*, code: str) -> FXCurrency:
        currency = FXCurrency.objects.filter(code=code.upper(), is_active=True).first()
        if not currency:
            raise ValidationError("Invalid currency code.")
        return currency

    @staticmethod
    @transaction.atomic
    def create(
        *,
        profile,
        name: str,
        asset_type_slug: str,
        currency_code: str,
        reason: str = CustomAsset.Reason.USER,
        requires_review: bool = False,
    ) -> CustomAsset:
        asset_type = CustomAssetService._get_asset_type_for_profile(
            profile=profile,
            slug=asset_type_slug,
        )
        currency = CustomAssetService._get_currency(code=currency_code)

        asset = Asset.objects.create(asset_type=asset_type)
        return CustomAsset.objects.create(
            asset=asset,
            owner=profile,
            name=name.strip(),
            currency=currency,
            reason=reason,
            requires_review=requires_review,
        )

    @staticmethod
    @transaction.atomic
    def update(
        *,
        custom_asset: CustomAsset,
        name: str | None = None,
        currency_code: str | None = None,
        requires_review: bool | None = None,
    ) -> CustomAsset:
        if name is not None:
            custom_asset.name = name.strip()

        if currency_code is not None:
            custom_asset.currency = CustomAssetService._get_currency(code=currency_code)

        if requires_review is not None:
            custom_asset.requires_review = requires_review

        custom_asset.save()
        return custom_asset

    @staticmethod
    @transaction.atomic
    def delete(*, custom_asset: CustomAsset):
        custom_asset.delete()

