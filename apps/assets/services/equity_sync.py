import logging
from decimal import Decimal, InvalidOperation

from assets.models.asset import Asset
from assets.models.details.equity_detail import EquityDetail
from apps.external_data.fmp.equity import fetch_stock_quote, fetch_stock_profile
from core.types import DomainType

logger = logging.getLogger(__name__)


class EquitySyncService:
    @staticmethod
    def _to_decimal(value) -> Decimal | None:
        """Helper to safely convert numeric values to Decimal."""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return None

    @staticmethod
    def sync(asset: Asset) -> bool:
        """
        Fetch data for an equity asset (stocks, ETFs, mutual funds, REITs, etc.)
        and update its EquityDetail.
        Returns True if sync succeeded, False otherwise.
        """
        if asset.asset_type != DomainType.EQUITY:
            logger.warning(
                f"Asset {asset.symbol} is not an equity, skipping sync")
            return False

        # Fetch external data
        quote = fetch_stock_quote(asset.symbol)
        profile = fetch_stock_profile(asset.symbol)

        if not quote or not profile:
            logger.warning(f"Missing equity data for {asset.symbol}")
            return False

        # Ensure detail exists
        detail, _ = EquityDetail.objects.get_or_create(asset=asset)

        try:
            # --- Profile fields ---
            detail.exchange = profile.get("exchangeShortName")
            detail.exchange_full_name = profile.get("exchange")
            detail.currency = profile.get("currency")
            detail.country = profile.get("country")
            detail.cusip = profile.get("cusip")
            detail.isin = profile.get("isin")
            detail.ipo_date = profile.get("ipoDate")

            detail.industry = profile.get("industry")
            detail.sector = profile.get("sector")
            detail.is_etf = bool(profile.get("isEtf", False))
            detail.is_adr = bool(profile.get("isAdr", False))
            detail.is_mutual_fund = bool(profile.get("isFund", False))

            # --- Quote fields ---
            detail.last_price = EquitySyncService._to_decimal(
                quote.get("price"))
            detail.open_price = EquitySyncService._to_decimal(
                quote.get("open"))
            detail.high_price = EquitySyncService._to_decimal(
                quote.get("dayHigh"))
            detail.low_price = EquitySyncService._to_decimal(
                quote.get("dayLow"))
            detail.previous_close_price = EquitySyncService._to_decimal(
                quote.get("previousClose"))

            detail.volume = quote.get("volume")
            detail.average_volume = quote.get("avgVolume")
            detail.market_cap = quote.get("marketCap")
            detail.shares_outstanding = quote.get("sharesOutstanding")
            detail.beta = EquitySyncService._to_decimal(quote.get("beta"))

            # --- Valuation ratios ---
            detail.eps = EquitySyncService._to_decimal(quote.get("eps"))
            detail.pe_ratio = EquitySyncService._to_decimal(quote.get("pe"))
            detail.pb_ratio = EquitySyncService._to_decimal(
                quote.get("priceToBook"))
            detail.ps_ratio = EquitySyncService._to_decimal(
                quote.get("priceToSales"))
            detail.peg_ratio = EquitySyncService._to_decimal(
                quote.get("pegRatio"))

            # --- Dividend info ---
            detail.dividend_per_share = EquitySyncService._to_decimal(
                profile.get("lastDiv"))
            detail.dividend_yield = EquitySyncService._to_decimal(
                quote.get("yield"))
            detail.dividend_frequency = profile.get("dividendFrequency")
            detail.ex_dividend_date = profile.get("exDividendDate")
            detail.dividend_payout_ratio = EquitySyncService._to_decimal(
                profile.get("payoutRatio"))

            # --- Mutual fund specifics ---
            detail.nav = EquitySyncService._to_decimal(profile.get("nav"))
            detail.expense_ratio = EquitySyncService._to_decimal(
                profile.get("expenseRatio"))
            detail.fund_family = profile.get("fundFamily")
            detail.fund_category = profile.get("category")
            detail.inception_date = profile.get("inceptionDate")
            detail.total_assets = profile.get("totalAssets")
            detail.turnover_ratio = EquitySyncService._to_decimal(
                profile.get("turnover"))

            # --- ETF specifics ---
            detail.underlying_index = profile.get("underlyingIndex")
            detail.aum = profile.get("aum")
            detail.holdings_count = profile.get("holdingsCount")
            detail.tracking_error = EquitySyncService._to_decimal(
                profile.get("trackingError"))

            # --- Optional ESG ---
            detail.esg_score = EquitySyncService._to_decimal(
                profile.get("esgScore"))
            detail.carbon_intensity = EquitySyncService._to_decimal(
                profile.get("carbonIntensity"))

            # Mark as synced
            detail.is_custom = False
            detail.save()

            logger.info(f"Synced equity {asset.symbol}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to sync equity {asset.symbol}: {e}", exc_info=True)
            return False
