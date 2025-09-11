import logging
from assets.models.asset import Asset
from assets.models.details.metal_detail import MetalDetail
from external_data.fmp.metals import fetch_metal_quote
from core.types import DomainType

logger = logging.getLogger(__name__)


class MetalSyncService:
    @staticmethod
    def sync(asset: Asset) -> bool:
        """
        Fetch data for a metal asset and update its MetalDetail.
        Returns True if sync succeeded, False otherwise.
        """
        if asset.asset_type != DomainType.METAL:
            logger.warning(
                f"Asset {asset.symbol} is not a metal, skipping sync")
            return False

        quote = fetch_metal_quote(asset.symbol)
        if not quote:
            logger.warning(f"No metal data returned for {asset.symbol}")
            return False

        detail, _ = MetalDetail.objects.get_or_create(asset=asset)

        try:
            for field, value in quote.items():
                setattr(detail, field, value)

            detail.is_custom = False
            detail.save()
            logger.info(f"Synced metal {asset.symbol}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to sync metal {asset.symbol}: {e}", exc_info=True)
            return False
