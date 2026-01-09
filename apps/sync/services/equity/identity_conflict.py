import logging

from django.db import transaction

from assets.models.asset_core import Asset, AssetIdentifier, AssetType
from assets.models.profiles.equity_profile import EquityProfile

logger = logging.getLogger(__name__)


class EquityIdentityConflictService:
    """
    Resolves equity identity conflicts.

    Rules:
    - Old asset is permanently deactivated
    - A NEW asset is created
    - Ticker is reused
    - Historical assets are never modified
    """

    @transaction.atomic
    def resolve(self, asset: Asset) -> Asset:
        ticker_ident = asset.identifiers.get(
            id_type=AssetIdentifier.IdentifierType.TICKER
        )
        ticker = ticker_ident.value.upper()

        # ----------------------------------
        # Deactivate old asset
        # ----------------------------------
        profile, _ = EquityProfile.objects.get_or_create(asset=asset)
        profile.is_actively_trading = False
        profile.identity_conflict = True
        profile.save(update_fields=[
            "is_actively_trading",
            "identity_conflict",
        ])

        # ----------------------------------
        # Create NEW asset
        # ----------------------------------
        equity_type = AssetType.objects.get(slug="equity")

        new_asset = Asset.objects.create(
            asset_type=equity_type,
        )

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
            "[EQUITY_IDENTITY_CONFLICT] ticker=%s old=%s new=%s",
            ticker,
            asset.id,
            new_asset.id,
        )

        return new_asset
