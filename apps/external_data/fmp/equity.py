import requests
import logging
from django.conf import settings
from external_data.fmp.normalize import normalize_fmp_data
from external_data.fmp.mappings.equities import EQUITY_PROFILE_MAP, EQUITY_QUOTE_MAP

logger = logging.getLogger(__name__)
FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE = "https://financialmodelingprep.com/api/v3"


def fetch_equity_profile(symbol: str) -> dict | None:
    """
    Fetch equity profile (classification, dividends, fund/ETF metadata).
    Returns normalized dict matching EquityDetail fields.
    """
    url = f"{FMP_BASE}/profile/{symbol}?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        d = data[0]
        return normalize_fmp_data(d, EQUITY_PROFILE_MAP)
    except Exception as e:
        logger.warning(f"Failed to fetch equity profile for {symbol}: {e}")
        return None


def fetch_equity_quote(symbol: str) -> dict | None:
    """
    Fetch equity quote (latest price, volume, valuation ratios).
    Returns normalized dict matching EquityDetail fields.
    """
    url = f"{FMP_BASE}/quote/{symbol}?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        d = data[0]
        return normalize_fmp_data(d, EQUITY_QUOTE_MAP)
    except Exception as e:
        logger.warning(f"Failed to fetch equity quote for {symbol}: {e}")
        return None
