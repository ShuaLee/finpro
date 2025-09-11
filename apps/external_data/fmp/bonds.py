import requests
import logging
from django.conf import settings
from external_data.fmp.normalize import normalize_fmp_data
from external_data.fmp.mappings.bonds import BOND_PROFILE_MAP, BOND_QUOTE_MAP

logger = logging.getLogger(__name__)
FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE = "https://financialmodelingprep.com/api/v3"


def fetch_bond_profile(symbol: str) -> dict | None:
    """
    Fetch bond profile (issuer, identifiers, coupon, dates, size, rating).
    Returns a normalized dict matching BondDetail fields.
    """
    url = f"{FMP_BASE}/bond/profile/{symbol}?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        d = data[0] if isinstance(data, list) else data
        return normalize_fmp_data(d, BOND_PROFILE_MAP)
    except Exception as e:
        logger.warning(f"Failed to fetch bond profile for {symbol}: {e}")
        return None


def fetch_bond_quote(symbol: str) -> dict | None:
    """
    Fetch latest bond quote (price, yields, accrued interest).
    Returns a normalized dict matching BondDetail fields.
    """
    url = f"{FMP_BASE}/bond/price/{symbol}?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        d = data[0] if isinstance(data, list) else data
        return normalize_fmp_data(d, BOND_QUOTE_MAP)
    except Exception as e:
        logger.warning(f"Failed to fetch bond quote for {symbol}: {e}")
        return None
