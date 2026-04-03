from django.core.exceptions import ValidationError

from apps.assets.models import Asset, AssetType


class AssetService:
    @staticmethod
    def create_asset(
        *,
        asset_type: AssetType,
        name: str,
        symbol: str = "",
        description: str = "",
        data: dict | None = None,
        owner=None,
        is_active: bool = True,
    ) -> Asset:
        asset = Asset(
            asset_type=asset_type,
            owner=owner,
            name=(name or "").strip(),
            symbol=(symbol or "").strip().upper(),
            description=(description or "").strip(),
            data=data or {},
            is_active=is_active,
        )
        asset.save()
        return asset

    @staticmethod
    def create_custom_asset(
        *,
        profile,
        asset_type: AssetType,
        name: str,
        symbol: str = "",
        description: str = "",
        data: dict | None = None,
        is_active: bool = True,
    ) -> Asset:
        return AssetService.create_asset(
            asset_type=asset_type,
            owner=profile,
            name=name,
            symbol=symbol,
            description=description,
            data=data,
            is_active=is_active,
        )

    @staticmethod
    def update_asset(
        *,
        asset: Asset,
        profile,
        asset_type: AssetType | None = None,
        name: str | None = None,
        symbol: str | None = None,
        description: str | None = None,
        data: dict | None = None,
        is_active: bool | None = None,
    ) -> Asset:
        if not asset.is_public and asset.owner != profile:
            raise ValidationError("You cannot edit another user's private asset.")

        if asset_type is not None:
            asset.asset_type = asset_type
        if name is not None:
            asset.name = name
        if symbol is not None:
            asset.symbol = symbol
        if description is not None:
            asset.description = description
        if data is not None:
            asset.data = data
        if is_active is not None:
            asset.is_active = is_active

        asset.save()
        return asset

    @staticmethod
    def deactivate_asset(*, asset: Asset, profile) -> Asset:
        if not asset.is_public and asset.owner != profile:
            raise ValidationError("You cannot deactivate another user's private asset.")
        asset.is_active = False
        asset.save(update_fields=["is_active", "updated_at"])
        return asset
