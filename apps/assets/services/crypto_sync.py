import logging
from decimal import Decimal

from assets.models.asset import Asset
from assets.models.details.crypto_detail import CryptoDetail
from core.types import DomainType
from external_data.fmp.crypto import fetch_crypto_quote, fetch_crypto_profile

logger = logging.getLogger(__name__)


class CryptoSyncService:
    @staticmethod
    def sync(asset: Asset) -> bool:
        """
        Fetch data for a crypto asset and update its CryptoDetail.
        Returns True if sync succeeded, False otherwise.
        """
        if asset.asset_type != DomainType.CRYPTO:
            logger.warning(
                f"Asset {asset.symbol} is not a crypto, skipping sync")
            return False

        # Step 1: Fetch profile (metadata)
        profile = fetch_crypto_profile(asset.symbol)
        if not profile:
            logger.warning(
                f"No profile found for crypto symbol {asset.symbol}")
            return False

        # Step 2: Fetch quote (market data)
        quote = fetch_crypto_quote(asset.symbol)
        if not quote:
            logger.warning(f"Missing crypto data for {asset.symbol}")
            return False

        # Step 3: Ensure detail exists
        detail, _ = CryptoDetail.objects.get_or_create(asset=asset)

        try:
            # --- Profile fields ---
            detail.exchange = profile.get("exchange")
            detail.description = profile.get("description")
            detail.website = profile.get("website")
            detail.logo_url = profile.get("logo_url")

            # --- Quote fields ---
            detail.currency = quote.get("currency", "USD")
            detail.decimals = quote.get("decimals", 8)

            detail.last_price = quote.get("last_price")
            detail.market_cap = quote.get("market_cap")
            detail.volume_24h = quote.get("volume_24h")
            detail.circulating_supply = quote.get("circulating_supply")
            detail.total_supply = quote.get("total_supply")

            detail.day_high = quote.get("day_high")
            detail.day_low = quote.get("day_low")
            detail.year_high = quote.get("year_high")
            detail.year_low = quote.get("year_low")

            detail.open_price = quote.get("open_price")
            detail.previous_close = quote.get("previous_close")
            detail.changes_percentage = quote.get("changes_percentage")

            # --- Custom/system flags ---
            detail.is_custom = False

            detail.save()
            logger.info(f"Synced crypto {asset.symbol}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to sync crypto {asset.symbol}: {e}", exc_info=True)
            return False
