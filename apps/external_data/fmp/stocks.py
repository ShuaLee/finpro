import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)
FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE = "https://financialmodelingprep.com/api/v3"


def fetch_stock_quote(symbol: str) -> dict | None:
    """
    Fetch latest stock quote for a given symbol from FMP.
    Example keys: price, volume, avgVolume, changesPercentage, etc.
    """
    url = f"{FMP_BASE}/quote/{symbol}?apikey={FMP_API_KEY}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data[0] if data else None
    except Exception as e:
        logger.warning(f"Failed to fetch stock quote for {symbol}: {e}")
        return None


def fetch_stock_profile(symbol: str) -> dict | None:
    """
    Fetch company profile for a given stock symbol from FMP.
    Example keys: exchangeShortName, currency, sector, industry, isEtf, isAdr.
    """
    url = f"{FMP_BASE}/profile/{symbol}?apikey={FMP_API_KEY}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data[0] if data else None
    except Exception as e:
        logger.warning(f"Failed to fetch stock profile for {symbol}: {e}")
        return None
