from decimal import Decimal
import logging
from assets.models.asset import Asset, AssetType
from assets.models.stock_detail import StockDetail
from external_data.fmp.stocks import fetch_stock_quote, fetch_stock_profile

logger = logging.getLogger(__name__)


class StockSyncService:
    @staticmethod
    def sync(asset: Asset) -> bool:
        """
        Fetch data for a stock asset and update its StockDetail.
        Returns True if sync succeeded, False otherwise.
        """
        if asset.asset_type != AssetType.STOCK:
            logger.warning(f"Asset {asset.symbol} is not a stock, skipping sync")
            return False

        # Fetch external data
        quote = fetch_stock_quote(asset.symbol)
        profile = fetch_stock_profile(asset.symbol)

        if not quote or not profile:
            logger.warning(f"Missing stock data for {asset.symbol}")
            return False

        # Ensure detail exists
        detail, _ = StockDetail.objects.get_or_create(asset=asset)

        try:
            # Map profile fields
            detail.exchange = profile.get("exchangeShortName")
            detail.currency = profile.get("currency")
            detail.industry = profile.get("industry")
            detail.sector = profile.get("sector")
            detail.is_etf = bool(profile.get("isEtf", False))
            detail.is_adr = bool(profile.get("isAdr", False))

            # Map quote fields
            detail.last_price = Decimal(str(quote.get("price") or "0"))
            detail.volume = quote.get("volume")
            detail.average_volume = quote.get("avgVolume")
            detail.pe_ratio = Decimal(str(quote.get("pe") or "0")) if quote.get("pe") else None

            # Calculate dividend yield if possible
            last_div = profile.get("lastDiv")
            if last_div and detail.last_price and detail.last_price > 0:
                detail.dividend_yield = Decimal(str(last_div)) * 4 / detail.last_price
            else:
                detail.dividend_yield = None

            detail.is_custom = False
            detail.save()
            logger.info(f"Synced stock {asset.symbol}")
            return True

        except Exception as e:
            logger.error(f"Failed to sync stock {asset.symbol}: {e}", exc_info=True)
            return False
