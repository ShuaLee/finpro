import logging
from decimal import Decimal

from assets.models.asset import Asset
from assets.models.bond_detail import BondDetail
from external_data.fmp.bonds import fetch_bond_quote, fetch_bond_profile
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
            logger.warning(f"Asset {asset.symbol} is not a bond, skipping sync")
            return False

        # Fetch external data
        quote = fetch_bond_quote(asset.symbol)
        profile = fetch_bond_profile(asset.symbol)

        if not quote or not profile:
            logger.warning(f"Missing bond data for {asset.symbol}")
            return False

        # Ensure detail exists
        detail, _ = BondDetail.objects.get_or_create(asset=asset)

        try:
            # Map profile fields
            detail.issuer = profile.get("issuer")
            detail.currency = profile.get("currency")
            detail.coupon_rate = (
                Decimal(str(profile.get("couponRate")))
                if profile.get("couponRate") is not None
                else None
            )
            detail.maturity_date = profile.get("maturityDate")
            detail.rating = profile.get("rating")

            # Map quote fields
            price_val = quote.get("price")
            detail.last_price = (
                Decimal(str(price_val)) if price_val is not None else None
            )

            detail.is_custom = False
            detail.save()
            logger.info(f"Synced bond {asset.symbol}")
            return True

        except Exception as e:
            logger.error(f"Failed to sync bond {asset.symbol}: {e}", exc_info=True)
            return False
