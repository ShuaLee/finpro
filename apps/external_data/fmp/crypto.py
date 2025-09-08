import requests
import logging
from django.conf import settings
from decimal import Decimal

logger = logging.getLogger(__name__)
FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE = "https://financialmodelingprep.com/api/v3"


def fetch_crypto_quote(symbol: str) -> dict | None:
    """
    Fetch latest crypto quote from FMP.
    Example keys: price, currency, etc.
    """
    url = f"{FMP_BASE}/quote/{symbol}?apikey={FMP_API_KEY}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if not data:
            return None
        return {
            "price": Decimal(str(data[0].get("price", "0"))),
            "currency": data[0].get("currency", "USD"),
            # decimals are not always provided, default fallback
            "decimals": 8,
        }
    except Exception as e:
        logger.warning(f"Failed to fetch crypto {symbol}: {e}")
        return None
