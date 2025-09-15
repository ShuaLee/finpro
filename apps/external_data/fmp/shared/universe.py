import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)
FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE = "https://financialmodelingprep.com/api/v3"

def fetch_equity_universe() -> list[dict]:
    """Fetch all listed equities (symbol + metadata)."""
    url = f"{FMP_BASE}/stock/list?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json() or []
    except Exception as e:
        logger.error(f"Failed to fetch equity universe: {e}")
        return []

def fetch_crypto_universe() -> list[dict]:
    """Fetch all supported cryptos."""
    url = f"{FMP_BASE}/cryptocurrency/list?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json() or []
    except Exception as e:
        logger.error(f"Failed to fetch crypto universe: {e}")
        return []
