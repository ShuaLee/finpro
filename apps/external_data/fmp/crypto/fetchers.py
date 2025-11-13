import logging
import requests
from django.conf import settings

from external_data.fmp.shared.normalize import normalize_fmp_data
from external_data.fmp.crypto.utils import split_crypto_pair, clean_crypto_name
from external_data.fmp.crypto.mappings import CRYPTO_MAP

logger = logging.getLogger(__name__)

FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE = "https://financialmodelingprep.com/stable"

# -------------------------------------------------------------------
# 1. Single-Asset Quote (Full)
# -------------------------------------------------------------------


def fetch_crypto_quote(symbol: str) -> dict | None:
    """
    Fetch full identity + price data.
    This replaces BOTH 'profile' and 'quote' behaviors.
    """
    url = f"{FMP_BASE}/quote?symbol={symbol}&apikey={FMP_API_KEY}"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
    except Exception as e:
        logger.warning(f"Failed to fetch crypto quote for {symbol}: {e}")
        return None

    raw = data[0]
    normalized = normalize_fmp_data(raw, CRYPTO_MAP)

    # Post-processing: split BTCUSD → BTC / USD
    base, quote = split_crypto_pair(symbol)
    normalized["asset__symbol"] = base
    normalized["quote_currency"] = quote or "USD"

    # Clean name: "Bitcoin USD" → "Bitcoin"
    if "asset__name" in normalized:
        normalized["asset__name"] = clean_crypto_name(
            normalized["asset__name"])

    return normalized


# -------------------------------------------------------------------
# 2. Short Quote (price only) — for fast valuation updates
# -------------------------------------------------------------------

def fetch_crypto_quote_short(symbol: str) -> dict | None:
    url = f"{FMP_BASE}/quote-short?symbol={symbol}&apikey={FMP_API_KEY}"

    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
    except Exception as e:
        logger.warning(f"Failed to fetch crypto short quote for {symbol}: {e}")
        return None

    # The short quote only contains symbol, price, change, volume
    return normalize_fmp_data(data[0], {
        "symbol": "asset__symbol",
        "price": "last_price",
    })


# -------------------------------------------------------------------
# 3. Bulk Quotes (for batch updating market data cache)
# -------------------------------------------------------------------

def fetch_crypto_quotes_bulk() -> dict:
    """
    Returns a dict:
    {
        "BTCUSD": {"last_price": Decimal("..."), ...},
        "ETHUSD": {...},
        ...
    }
    """
    url = f"{FMP_BASE}/batch-crypto-quotes?apikey={FMP_API_KEY}"

    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        records = r.json() or []
    except Exception as e:
        logger.warning(f"Failed to fetch bulk crypto quotes: {e}")
        return {}

    result = {}
    for rec in records:
        symbol = rec.get("symbol")
        if not symbol:
            continue
        result[symbol] = normalize_fmp_data(rec, CRYPTO_MAP)

    return result


# -------------------------------------------------------------------
# 4. Universe List (for seeding + rename + delist detection)
# -------------------------------------------------------------------

def fetch_crypto_universe() -> list[dict]:
    """
    Returns the FMP universe listing:
    [
        {
            "symbol": "BTCUSD",
            "name": "Bitcoin USD",
            "exchange": "CRYPTO",
            "icoDate": "...",
            "circulatingSupply": ...,
            "totalSupply": ...
        },
        ...
    ]
    """
    url = f"{FMP_BASE}/cryptocurrency-list?apikey={FMP_API_KEY}"

    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json() or []
    except Exception as e:
        logger.error(f"Failed to fetch crypto universe: {e}")
        return []
