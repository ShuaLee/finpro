import requests
import logging
from django.conf import settings
from external_data.fmp.normalize import normalize_fmp_data
from external_data.fmp.mappings.metals import METAL_QUOTE_MAP

logger = logging.getLogger(__name__)
FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE = "https://financialmodelingprep.com/api/v3"


def fetch_metal_quote(symbol: str) -> dict | None:
    """
    Fetch latest precious metal quote (e.g., gold, silver, platinum).
    Returns normalized dict matching MetalDetail fields.
    """
    url = f"{FMP_BASE}/quote/{symbol}?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        d = data[0]
        return normalize_fmp_data(d, METAL_QUOTE_MAP)
    except Exception as e:
        logger.warning(f"Failed to fetch metal quote for {symbol}: {e}")
        return None
