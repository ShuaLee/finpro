import logging
from assets.models.asset import Asset
from assets.models.details.bond_detail import BondDetail
from external_data.fmp.bonds import fetch_bond_profile, fetch_bond_quote
from core.types import DomainType

logger = logging.getLogger(__name__)


class BondSyncService:
    @staticmethod
    def sync(asset: Asset) -> bool:
        """
        Fetch data for a bond asset and update its BondDetail.
        Returns True if sync succeeded, False otherwise.
        """
        if asset.asset_type != DomainType.BOND:
            logger.warning(
                f"Asset {asset.symbol} is not a bond, skipping sync")
            return False

        profile = fetch_bond_profile(asset.symbol) or {}
        quote = fetch_bond_quote(asset.symbol) or {}

        if not profile and not quote:
            logger.warning(f"No bond data returned for {asset.symbol}")
            return False

        detail, _ = BondDetail.objects.get_or_create(asset=asset)

        try:
            # Merge profile + quote
            merged = {**profile, **quote}
            for field, value in merged.items():
                setattr(detail, field, value)

            detail.is_custom = False
            detail.save()
            logger.info(f"Synced bond {asset.symbol}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to sync bond {asset.symbol}: {e}", exc_info=True)
            return False
