import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)
FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE = "https://financialmodelingprep.com/api/v3"


def fetch_bond_quote(symbol: str) -> dict | None:
    url = f"{FMP_BASE}/quote/{symbol}?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        return data[0] if data else None
    except Exception as e:
        logger.warning(f"Failed to fetch bond quote for {symbol}: {e}")
        return None


def fetch_bond_profile(symbol: str) -> dict | None:
    url = f"{FMP_BASE}/bond-profile/{symbol}?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        return data[0] if data else None
    except Exception as e:
        logger.warning(f"Failed to fetch bond profile for {symbol}: {e}")
        return None
