import requests
import logging
from django.conf import settings

from external_data.fmp.shared.normalize import normalize_fmp_data
from external_data.fmp.bonds.mappings import BOND_PROFILE_MAP, BOND_QUOTE_MAP

logger = logging.getLogger(__name__)

FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE = "https://financialmodelingprep.com/api/v3"


# ------------------------------
# Single fetchers
# ------------------------------
def fetch_bond_profile(symbol: str) -> dict | None:
    """
    Fetch bond profile from FMP and normalize fields.
    (issuer, type, identifiers, etc.)
    """
    url = f"{FMP_BASE}/bond/profile/{symbol}?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        d = data[0]
        return normalize_fmp_data(d, BOND_PROFILE_MAP)
    except Exception as e:
        logger.warning(f"Failed to fetch bond profile for {symbol}: {e}")
        return None


def fetch_bond_quote(symbol: str) -> dict | None:
    """
    Fetch latest bond quote from FMP and normalize fields.
    (price, yields, risk metrics, etc.)
    """
    url = f"{FMP_BASE}/bond/quote/{symbol}?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        d = data[0]
        return normalize_fmp_data(d, BOND_QUOTE_MAP)
    except Exception as e:
        logger.warning(f"Failed to fetch bond quote for {symbol}: {e}")
        return None


# ------------------------------
# Bulk fetchers
# ------------------------------
def bulk_fetch_bond_quotes(symbols: list[str]) -> dict[str, dict]:
    """
    Bulk fetch quotes for multiple bonds.
    Returns {symbol: normalized_data}.
    """
    if not symbols:
        return {}

    joined = ",".join(symbols)
    url = f"{FMP_BASE}/bond/quote/{joined}?apikey={FMP_API_KEY}"

    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json() or []
        results: dict[str, dict] = {}

        for d in data:
            sym = d.get("symbol")
            if not sym:
                continue
            results[sym] = normalize_fmp_data(d, BOND_QUOTE_MAP)

        return results
    except Exception as e:
        logger.error(f"Bulk bond quote fetch failed for {symbols}: {e}")
        return {}
