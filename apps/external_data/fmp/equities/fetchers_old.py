import requests
import logging
from django.conf import settings

from external_data.fmp.shared.normalize import normalize_fmp_data
from external_data.fmp.equities.mappings import EQUITY_PROFILE_MAP, EQUITY_QUOTE_MAP

logger = logging.getLogger(__name__)

FMP_API_KEY = settings.FMP_API_KEY

FMP_BASE = "https://financialmodelingprep.com/api/v3"
FMP_STABLE_BASE = "https://financialmodelingprep.com/stable"
FMP_BULK_PROFILE = f"{FMP_STABLE_BASE}/profile-bulk"


# ------------------------------
# Single Fetchers
# ------------------------------
def fetch_equity_profile_raw(symbol: str) -> dict | None:
    """
    Fetch the raw equity profile from FMP without normalization.
    Returns the unmodified JSON dict (useful for identifier hydration).
    """
    url = f"{FMP_STABLE_BASE}/profile?symbol={symbol}&apikey={FMP_API_KEY}"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None

        # Return only the exact symbol match
        for item in data:
            if item.get("symbol", "").upper() == symbol.upper():
                return item
        return None
    except Exception as e:
        logger.warning(f"Failed to fetch raw profile for {symbol}: {e}")
        return None


def fetch_equity_profile(symbol: str) -> dict | None:
    """
    Fetches and normalizes the equity profile for the exact symbol match
    from a list of possible matches returned by FMP.
    """
    url = f"{FMP_STABLE_BASE}/profile?symbol={symbol}&apikey={FMP_API_KEY}"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        if not isinstance(data, list) or not data:
            return None

        symbol_upper = symbol.upper()

        # Return the exact symbol match
        for item in data:
            if not isinstance(item, dict):
                continue
            if item.get("symbol", "").upper() == symbol_upper:
                return normalize_fmp_data(item, EQUITY_PROFILE_MAP)

        return None

    except Exception as e:
        logger.warning(f"Failed to fetch profile for {symbol}: {e}")
        return None


def fetch_equity_profiles_multi(symbol: str) -> list[dict]:
    """
    Fetch multiple equity profiles from FMP for a symbol query (e.g., FRO),
    using the STABLE API. Returns a list of normalized profile dictionaries.

    This handles cases where the API returns multiple stocks with similar symbols.
    """
    url = f"{FMP_STABLE_BASE}/profile?symbol={symbol}&apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        if not data or not isinstance(data, list):
            return []

        return [
            normalize_fmp_data(d, EQUITY_PROFILE_MAP)
            for d in data
            if isinstance(d, dict) and d.get("symbol")
        ]
    except Exception as e:
        logger.warning(
            f"Failed to fetch multi equity profiles for {symbol}: {e}")
        return []


def fetch_equity_quote(symbol: str) -> dict | None:
    """
    Fetch and normalize latest quote for a single equity.
    """
    url = f"{FMP_STABLE_BASE}/quote?symbol={symbol}&apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data or not isinstance(data, list):
            logger.warning(f"No quote data for {symbol}. Response: {r.text}")
            return None
        return normalize_fmp_data(data[0], EQUITY_QUOTE_MAP)
    except Exception as e:
        logger.warning(f"Failed to fetch equity quote for {symbol}: {e}")
        return None


# ------------------------------
# Bulk Fetchers
# ------------------------------
def fetch_equity_quotes_bulk(symbols: list[str]) -> list[dict]:
    """
    Fetch bulk quotes for a list of symbols.
    """
    if not symbols:
        return []
    url = f"{FMP_STABLE_BASE}/quote?symbol={','.join(symbols)}&apikey={FMP_API_KEY}"
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
    Fetch a bulk chunk of equity profiles from FMP STABLE endpoint.
    """
    url = f"{FMP_BULK_PROFILE}?part={part}&apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        data = r.json()
        return [
            normalize_fmp_data(d, EQUITY_PROFILE_MAP)
            for d in data if d
        ]
    except Exception as e:
        logger.warning(
            f"Failed bulk equity profile fetch for part {part}: {e}")
        return []


# ------------------------------
# Universe (for seeding database)
# ------------------------------
def fetch_equity_universe() -> list[dict]:
    """
    Fetch all known equity symbols (lightweight symbol list).
    """
    url = f"{FMP_STABLE_BASE}/stock-list?apikey={FMP_API_KEY}"
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
    Fetch equity profile by ISIN using FMP STABLE endpoint.
    """
    url = f"{FMP_STABLE_BASE}/search-isin?isin={isin}&apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data or not isinstance(data, list):
            return None
        return normalize_fmp_data(data[0], EQUITY_PROFILE_MAP)
    except Exception as e:
        logger.warning(f"Failed ISIN lookup for {isin}: {e}")
        return None


def fetch_equity_by_cusip(cusip: str) -> dict | None:
    """
    Fetch equity profile by CUSIP using FMP STABLE endpoint.
    """
    url = f"{FMP_STABLE_BASE}/search-cusip?cusip={cusip}&apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data or not isinstance(data, list):
            return None
        return normalize_fmp_data(data[0], EQUITY_PROFILE_MAP)
    except Exception as e:
        logger.warning(f"Failed CUSIP lookup for {cusip}: {e}")
        return None


def fetch_equity_by_cik(cik: str) -> dict | None:
    """
    Fetch equity profile by CIK using FMP STABLE endpoint.
    """
    url = f"{FMP_STABLE_BASE}/profile-cik?cik={cik}&apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data or not isinstance(data, list):
            return None
        return normalize_fmp_data(data[0], EQUITY_PROFILE_MAP)
    except Exception as e:
        logger.warning(f"Failed CIK lookup for {cik}: {e}")
        return None
