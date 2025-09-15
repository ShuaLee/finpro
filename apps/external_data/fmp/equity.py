import requests
import logging
from django.conf import settings
from external_data.fmp.normalize import normalize_fmp_data
from external_data.fmp.mappings.equities import EQUITY_PROFILE_MAP, EQUITY_QUOTE_MAP

logger = logging.getLogger(__name__)

FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE = "https://financialmodelingprep.com/api/v3"


# ------------------------------
# Single-Symbol Fetchers
# ------------------------------
def fetch_equity_profile(symbol: str) -> dict | None:
    """
    Fetch profile for one equity (slow-changing fields).
    """
    url = f"{FMP_BASE}/profile/{symbol}?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        return normalize_fmp_data(data[0], EQUITY_PROFILE_MAP)
    except Exception as e:
        logger.warning(f"Profile fetch failed for {symbol}: {e}")
        return None


def fetch_equity_quote(symbol: str) -> dict | None:
    """
    Fetch quote for one equity (fast-changing fields).
    """
    url = f"{FMP_BASE}/quote/{symbol}?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        return normalize_fmp_data(data[0], EQUITY_QUOTE_MAP)
    except Exception as e:
        logger.warning(f"Quote fetch failed for {symbol}: {e}")
        return None


# ------------------------------
# Bulk Fetchers
# ------------------------------
def fetch_equity_profiles_bulk(symbols: list[str]) -> list[dict]:
    """
    Fetch profiles for multiple symbols at once.
    """
    if not symbols:
        return []
    url = f"{FMP_BASE}/profile/{','.join(symbols)}?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        return [normalize_fmp_data(d, EQUITY_PROFILE_MAP) for d in data] if data else []
    except Exception as e:
        logger.warning(f"Bulk profile fetch failed: {e}")
        return []


def fetch_equity_quotes_bulk(symbols: list[str]) -> list[dict]:
    """
    Fetch quotes for multiple symbols at once.
    """
    if not symbols:
        return []
    url = f"{FMP_BASE}/quote/{','.join(symbols)}?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        return [normalize_fmp_data(d, EQUITY_QUOTE_MAP) for d in data] if data else []
    except Exception as e:
        logger.warning(f"Bulk quote fetch failed: {e}")
        return []
