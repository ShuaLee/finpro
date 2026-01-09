import logging
from django.db import transaction

from assets.models.asset_core import Asset, AssetIdentifier, AssetType
from assets.models.profiles.equity_profile import EquityProfile
from external_data.providers.fmp.client import FMP_PROVIDER

logger = logging.getLogger(__name__)


class EquityIdentityConflictService:
    """
    Resolve identity conflicts by:
    - Deactivating the old asset
    - Creating a NEW asset with the same ticker
    """

    @transaction.atomic
    def resolve(self, asset: Asset) -> Asset:
        ticker_ident = asset.identifiers.get(
            id_type=AssetIdentifier.IdentifierType.TICKER
        )
        ticker = ticker_ident.value.upper()

        # Deactivate old profile
        profile = EquityProfile.objects.get(asset=asset)
        profile.is_actively_trading = False
        profile.identity_conflict = True
        profile.save(update_fields=[
                     "is_actively_trading", "identity_conflict"])

        # Create new asset
        equity_type = AssetType.objects.get(slug="equity")
        new_asset = Asset.objects.create(asset_type=equity_type)

        AssetIdentifier.objects.create(
            asset=new_asset,
            id_type=AssetIdentifier.IdentifierType.TICKER,
            value=ticker,
        )

        EquityProfile.objects.create(
            asset=new_asset,
            is_actively_trading=True,
        )

        logger.warning(
            "[IDENTITY_RESOLVED] %s old_asset=%s new_asset=%s",
            ticker,
            asset.id,
            new_asset.id,
        )

        return new_asset
