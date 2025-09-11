import requests
import logging
from django.conf import settings
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)
FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE = "https://financialmodelingprep.com/api/v3"


def _to_decimal(value, default=None) -> Decimal | None:
    if value is None:
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default


def fetch_crypto_quote(symbol: str) -> dict | None:
    """
    Fetch latest crypto quote from FMP and normalize fields.
    Example keys: last_price, market_cap, volume_24h, circulating_supply, total_supply, etc.
    """
    url = f"{FMP_BASE}/quote/{symbol}?apikey={FMP_API_KEY}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if not data:
            return None
        d = data[0]

        return {
            # Market data
            "last_price": _to_decimal(d.get("price")),
            "currency": d.get("currency", "USD"),
            "market_cap": d.get("marketCap"),
            "volume_24h": d.get("volume"),
            "circulating_supply": _to_decimal(d.get("circulatingSupply")),
            # FMP quirk
            "total_supply": _to_decimal(d.get("sharesOutstanding")),
            "day_high": _to_decimal(d.get("dayHigh")),
            "day_low": _to_decimal(d.get("dayLow")),
            "year_high": _to_decimal(d.get("yearHigh")),
            "year_low": _to_decimal(d.get("yearLow")),
            "open_price": _to_decimal(d.get("open")),
            "previous_close": _to_decimal(d.get("previousClose")),
            "changes_percentage": _to_decimal(d.get("changesPercentage")),

            # Fallbacks
            "decimals": 8,  # FMP doesn’t expose decimals, assume 8
        }
    except Exception as e:
        logger.warning(f"Failed to fetch crypto quote for {symbol}: {e}")
        return None


def fetch_crypto_profile(symbol: str) -> dict | None:
    """
    Fetch crypto profile (metadata) from FMP and normalize fields.
    Example keys: description, website, logo_url, exchange.
    """
    url = f"{FMP_BASE}/profile/{symbol}?apikey={FMP_API_KEY}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if not data:
            return None
        d = data[0]

        return {
            "description": d.get("description"),
            "website": d.get("website"),
            "logo_url": d.get("image"),
            "exchange": d.get("exchange"),
        }
    except Exception as e:
        logger.warning(f"Failed to fetch crypto profile for {symbol}: {e}")
        return None
