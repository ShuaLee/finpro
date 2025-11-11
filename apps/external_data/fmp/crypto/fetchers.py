import requests
import logging
from django.conf import settings

from external_data.fmp.shared.normalize import normalize_fmp_data
from external_data.fmp.crypto.mappings import CRYPTO_MAP
logger = logging.getLogger(__name__)

FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE = "https://financialmodelingprep.com/stable"

# ------------------------------
#  Single Crypto Fetchers
# ------------------------------


def fetch_crypto_quote(symbol: str) -> dict | None:
    """
    Fetch detailed market data for a specific crypto symbol pair (e.g. BTCUSD).
    Returns normalized data dictionary if found, else None.
    """
    url = f"{FMP_BASE}/quote?symbol={symbol}&apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        return normalize_fmp_data(data[0], CRYPTO_MAP)
    except Exception as e:
        logger.warning(f"Failed to fetch crypto for {symbol}: {e}")
        return None


def fetch_crypto_quote_short(symbol: str) -> dict | None:
    """
    Fetch lightweight market data (price only) for quick valuation updates.
    """
    url = f"{FMP_BASE}/quote-short?symbol={symbol}&apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        return normalize_fmp_data(data[0], CRYPTO_MAP)
    except Exception as e:
        logger.warning(f"Failed to fetch crypto short quote for {symbol}: {e}")
        return None

# ------------------------------
#  Bulk / Batch Crypto Fetchers
# ------------------------------

# I dont know how FMP bulk works for crypto. This may not be right.


def fetch_crypto_quotes_bulk() -> list[dict]:
    """
    Fetch batch market data for multiple cryptocurrencies.
    Returns a list of quote dicts (like quote-short, but batched).
    """
    url = f"{FMP_BASE}/batch-crypto-quotes?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data or []
    except Exception as e:
        logger.warning(f"Failed to fetch bulk crypto quotes: {e}")
        return []

# ------------------------------
#  Universe / Listing Fetcher
# ------------------------------


def fetch_crypto_universe() -> list[dict]:
    """
    Fetch the complete cryptocurrency listing from FMP.
    Useful for seeding or updating supported crypto assets in DB.
    """
    url = f"{FMP_BASE}/cryptocurrency-list?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data or []
    except Exception as e:
        logger.error(f"Failed to fetch crypto universe: {e}")
        return []
