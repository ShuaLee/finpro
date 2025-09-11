import logging
from assets.models.asset import Asset
from assets.models.details.equity_detail import EquityDetail
from external_data.fmp.equity import fetch_equity_profile, fetch_equity_quote
from core.types import DomainType

logger = logging.getLogger(__name__)


class EquitySyncService:
    @staticmethod
    def sync(asset: Asset) -> bool:
        """
        Fetch data for an equity asset and update its EquityDetail.
        Returns True if sync succeeded, False otherwise.
        """
        if asset.asset_type != DomainType.EQUITY:
            logger.warning(
                f"Asset {asset.symbol} is not an equity, skipping sync")
            return False

        profile = fetch_equity_profile(asset.symbol) or {}
        quote = fetch_equity_quote(asset.symbol) or {}

        if not profile and not quote:
            logger.warning(f"No equity data returned for {asset.symbol}")
            return False

        detail, _ = EquityDetail.objects.get_or_create(asset=asset)

        try:
            merged = {**profile, **quote}
            for field, value in merged.items():
                setattr(detail, field, value)

            detail.is_custom = False
            detail.save()
            logger.info(f"Synced equity {asset.symbol}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to sync equity {asset.symbol}: {e}", exc_info=True)
            return False
