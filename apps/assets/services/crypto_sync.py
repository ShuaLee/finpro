from assets.models.asset import Asset
from assets.models.crypto_detail import CryptoDetail
from core.types import DomainType
from external_data.fmp.crypto import fetch_crypto_quote, fetch_crypto_profile

from decimal import Decimal

import logging

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

        # 🛡️ Step 1: Validate it is truly a crypto
        profile = fetch_crypto_profile(asset.symbol)
        if not profile:
            logger.warning(
                f"No profile found for crypto symbol {asset.symbol}")
            return False

        exchange = profile.get("exchangeShortName", "").lower()
        if exchange not in {"crypto", "binance", "coinbase", "kraken"}:
            logger.warning(
                f"Symbol {asset.symbol} (exchange: {exchange}) is not recognized as a crypto. "
                "Suggest adding it as a custom asset."
            )
            return False

        # ✅ Step 2: Fetch external quote
        quote = fetch_crypto_quote(asset.symbol)
        if not quote:
            logger.warning(f"Missing crypto data for {asset.symbol}")
            return False

        # ✅ Step 3: Ensure detail exists
        detail, _ = CryptoDetail.objects.get_or_create(asset=asset)

        try:
            detail.currency = quote.get("currency", "USD")
            detail.decimals = quote.get("decimals", 8)

            price = quote.get("price")
            detail.last_price = Decimal(
                str(price)) if price is not None else None

            detail.is_custom = False
            detail.save()
            logger.info(f"Synced crypto {asset.symbol}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to sync crypto {asset.symbol}: {e}", exc_info=True)
            return False
