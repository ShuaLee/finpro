import requests
import logging
from django.conf import settings

from external_data.fmp.shared.normalize import normalize_fmp_data
from external_data.fmp.metals.mappings import METAL_QUOTE_MAP

logger = logging.getLogger(__name__)

FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE = "https://financialmodelingprep.com/api/v3"


# ------------------------------
# Single fetchers
# ------------------------------
def fetch_metal_quote(symbol: str) -> dict | None:
    """
    Fetch latest precious metal quote (e.g., XAUUSD, XAGUSD) from FMP.
    """
    url = f"{FMP_BASE}/quote/{symbol}?apikey={FMP_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            return None

        d = data[0]
        return normalize_fmp_data(d, METAL_QUOTE_MAP)
    except Exception as e:
        logger.warning(f"Failed to fetch metal quote for {symbol}: {e}")
        return None


# ------------------------------
# Bulk fetchers
# ------------------------------
def bulk_fetch_metal_quotes(symbols: list[str]) -> dict[str, dict]:
    """
    Bulk fetch quotes for multiple metals.
    Returns {symbol: normalized_data}.
    """
    if not symbols:
        return {}

    joined = ",".join(symbols)
    url = f"{FMP_BASE}/quote/{joined}?apikey={FMP_API_KEY}"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json() or []
        results: dict[str, dict] = {}

        for d in data:
            sym = d.get("symbol")
            if not sym:
                continue
            results[sym] = normalize_fmp_data(d, METAL_QUOTE_MAP)

        return results
    except Exception as e:
        logger.error(f"Bulk metal quote fetch failed for {symbols}: {e}")
        return {}
