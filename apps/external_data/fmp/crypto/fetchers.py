import requests
import logging
from django.conf import settings
from decimal import Decimal, InvalidOperation

from external_data.fmp.shared.normalize import normalize_fmp_data
from external_data.fmp.crypto.mappings import CRYPTO_PROFILE_MAP, CRYPTO_QUOTE_MAP

logger = logging.getLogger(__name__)

FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE = "https://financialmodelingprep.com/api/v3"


def _to_decimal(value, default=None) -> Decimal | None:
    """Safe conversion to Decimal."""
    if value is None:
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default


# ------------------------------
# Single fetchers
# ------------------------------
def fetch_crypto_quote(symbol: str) -> dict | None:
    """
    Fetch latest crypto quote from FMP and normalize fields.
    """
    url = f"{FMP_BASE}/quote/{symbol}?apikey={FMP_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            return None
        d = data[0]

        normalized = normalize_fmp_data(d, CRYPTO_QUOTE_MAP)
        normalized.setdefault("decimals", 8)  # FMP doesn’t expose decimals
        return normalized
    except Exception as e:
        logger.warning(f"Failed to fetch crypto quote for {symbol}: {e}")
        return None


def fetch_crypto_profile(symbol: str) -> dict | None:
    """
    Fetch crypto profile (metadata) from FMP and normalize fields.
    """
    url = f"{FMP_BASE}/profile/{symbol}?apikey={FMP_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            return None
        d = data[0]
        return normalize_fmp_data(d, CRYPTO_PROFILE_MAP)
    except Exception as e:
        logger.warning(f"Failed to fetch crypto profile for {symbol}: {e}")
        return None


# ------------------------------
# Bulk fetchers
# ------------------------------
def bulk_fetch_crypto_quotes(symbols: list[str]) -> dict[str, dict]:
    """
    Bulk fetch crypto quotes for multiple symbols.
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
            normalized = normalize_fmp_data(d, CRYPTO_QUOTE_MAP)
            normalized.setdefault("decimals", 8)
            results[sym] = normalized

        return results
    except Exception as e:
        logger.error(f"Bulk crypto quote fetch failed for {symbols}: {e}")
        return {}
