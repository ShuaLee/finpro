# external_data/fmp/equities/fetchers.py

import requests
import logging
from django.conf import settings

from external_data.fmp.shared.normalize import normalize_fmp_data
from external_data.fmp.equities.mappings import EQUITY_PROFILE_MAP, EQUITY_QUOTE_MAP

logger = logging.getLogger(__name__)

FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE = "https://financialmodelingprep.com/api/v3"
FMP_BULK_PROFILE = "https://financialmodelingprep.com/stable/profile-bulk"


# ------------------------------
# Single Fetchers
# ------------------------------
def fetch_equity_profile_raw(symbol: str) -> dict | None:
    """
    Fetch the raw equity profile from FMP without normalization.
    Returns the unmodified JSON dict (useful for identifier hydration).
    """
    url = f"{FMP_BASE}/profile/{symbol}?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        return data[0]  # Return the first element of the list
    except Exception as e:
        logger.warning(f"Failed to fetch raw profile for {symbol}: {e}")
        return None


# ------------------------------
# Single Fetchers
# ------------------------------
def fetch_equity_profile(symbol: str) -> dict | None:
    url = f"{FMP_BASE}/profile/{symbol}?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        return normalize_fmp_data(data[0], EQUITY_PROFILE_MAP)
    except Exception as e:
        logger.warning(f"Failed to fetch equity profile for {symbol}: {e}")
        return None


def fetch_equity_quote(symbol: str) -> dict | None:
    url = f"{FMP_BASE}/quote/{symbol}?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        return normalize_fmp_data(data[0], EQUITY_QUOTE_MAP)
    except Exception as e:
        logger.warning(f"Failed to fetch equity quote for {symbol}: {e}")
        return None


# ------------------------------
# Bulk Fetchers
# ------------------------------
def fetch_equity_quotes_bulk(symbols: list[str]) -> list[dict]:
    if not symbols:
        return []
    url = f"{FMP_BASE}/quote/{','.join(symbols)}?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()
        return [normalize_fmp_data(d, EQUITY_QUOTE_MAP) for d in data if d]
    except Exception as e:
        logger.warning(f"Failed bulk equity quote fetch: {e}")
        return []


def fetch_equity_profiles_bulk(part: int = 0) -> list[dict]:
    """
    Fetch a bulk chunk of equity profiles from FMP.
    FMP splits the universe into parts (0, 1, 2, ...).
    Returns a list of normalized dicts.
    """
    url = f"{FMP_BULK_PROFILE}?part={part}&apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        data = r.json()
        return [
            normalize_fmp_data(d, EQUITY_PROFILE_MAP)
            for d in data
            if d
        ]
    except Exception as e:
        logger.warning(
            f"Failed bulk equity profile fetch for part {part}: {e}")
        return []


# ------------------------------
# Universe (for seeding database)
# ------------------------------
def fetch_equity_universe() -> list[dict]:
    url = f"{FMP_BASE}/stock/list?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data or []
    except Exception as e:
        logger.error(f"Failed to fetch equity universe: {e}")
        return []


# ------------------------------
# Identifier-based Fetchers
# ------------------------------

def fetch_equity_by_isin(isin: str) -> dict | None:
    """
    Fetch equity profile by ISIN using FMP.
    """
    url = f"{FMP_BASE}/stable/search-isin?isin={isin}&apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        return normalize_fmp_data(data[0], EQUITY_PROFILE_MAP)
    except Exception as e:
        logger.warning(f"Failed ISIN lookup for {isin}: {e}")
        return None


def fetch_equity_by_cusip(cusip: str) -> dict | None:
    """
    Fetch equity profile by CUSIP using FMP.
    """
    url = f"{FMP_BASE}/stable/search-cusip?cusip={cusip}&apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        return normalize_fmp_data(data[0], EQUITY_PROFILE_MAP)
    except Exception as e:
        logger.warning(f"Failed CUSIP lookup for {cusip}: {e}")
        return None


def fetch_equity_by_cik(cik: str) -> dict | None:
    """
    Fetch equity profile by CIK using FMP.
    """
    url = f"{FMP_BASE}/stable/profile-cik?cik={cik}&apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        return normalize_fmp_data(data[0], EQUITY_PROFILE_MAP)
    except Exception as e:
        logger.warning(f"Failed CIK lookup for {cik}: {e}")
        return None
