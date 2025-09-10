from django.conf import settings
from decimal import Decimal
import requests
import logging

logger = logging.getLogger(__name__)
FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE = "https://financialmodelingprep.com/api/v3"


def fetch_precious_metal_quote(symbol: str) -> dict | None:
    """
    Fetch latest precious metal price from FMP.
    Example symbols: XAUUSD (Gold), XAGUSD (Silver).
    """
    url = f"{FMP_BASE}/quote/{symbol}?apikey={FMP_API_KEY}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if not data:
            return None
        return {
            "price": Decimal(str(data[0].get("price", "0"))),
            "currency": data[0].get("currency", "USD"),
            "symbol": symbol.upper(),
            "unit": "oz",  # default unit
        }
    except Exception as e:
        logger.warning(f"Failed to fetch metal {symbol}: {e}")
        return None


def fetch_metal_profile(symbol: str) -> dict | None:
    """
    Fetch company/profile info to check exchange or classification of a metal symbol.
    """
    url = f"{FMP_BASE}/profile/{symbol}?apikey={FMP_API_KEY}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data[0] if data else None
    except Exception as e:
        logger.warning(f"Failed to fetch metal profile for {symbol}: {e}")
        return None
