import requests
import logging

from django.conf import settings

from decimal import Decimal

logger = logging.getLogger(__name__)

FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE = "https://financialmodelingprep.com/api/stable"


def fetch_fx_universe() -> list[dict]:
    """
    Fetch the complete list of forex pairs from FMP.

    Each entry looks like:
    {
        "symbol": "EURUSD",
        "fromCurrency": "EUR",
        "toCurrency": "USD",
        "fromName": "Euro",
        "toName": "US Dollar"
    }
    """
    url = f"{FMP_BASE}/forex-list?apikey={FMP_API_KEY}"

    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()

        if not isinstance(data, list):
            logger.warning(f"Unexpected forex-list response: {data}")
            return []

        return data

    except Exception as e:
        logger.error(f"Failed to fetch forex universe: {e}")
        return []


def fetch_fx_quote(base: str, quote: str) -> dict | None:
    """
    Fetch a single FX pair, BASE→QUOTE.

    Example:
        fetch_fx_quote("USD", "CAD")
    Returns:
    {
        "from": "USD",
        "to": "CAD",
        "rate": Decimal("1.35672"),
        "raw": {...original FMP response...}
    }
    """
    base = base.upper()
    quote = quote.upper()
    symbol = f"{base}{quote}"

    url = f"{FMP_BASE}/quote/{symbol}?apikey={FMP_API_KEY}"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        if not isinstance(data, list) or not data:
            logger.warning(f"Empty FX quote for {symbol}: {data}")
            return None

        price = data[0].get("price")
        if price is None:
            logger.warning(f"FX missing price for {symbol}: {data}")
            return None

        return {
            "from": base,
            "to": quote,
            "rate": Decimal(str(price)),
            "raw": data[0],
        }

    except Exception as e:
        logger.error(f"Failed to fetch FX quote for {symbol}: {e}")
        return None


def fetch_fx_quotes_bulk(symbols: list[str], short: bool = False) -> list[dict]:
    """
    Fetch FX quotes for multiple symbols, e.g.:

        ["EURUSD", "USDJPY", "CADCHF"]

    Returns:
    [
        {"from": "EUR", "to": "USD", "rate": Decimal("1.0893")},
        ...
    ]
    """
    if not symbols:
        return []

    url = f"{FMP_BASE}/batch-forex-quotes?apikey={FMP_API_KEY}"
    if short:
        url += "&short=true"

    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()

        results = []

        for d in data:
            symbol = d.get("symbol")
            price = d.get("price")

            if not symbol or price is None:
                continue

            # Infer base/quote from the symbol
            if len(symbol) % 2 != 0:
                # Skip malformed pairs
                continue

            mid = len(symbol) // 2
            base = symbol[:mid].upper()
            quote = symbol[mid:].upper()

            results.append({
                "from": base,
                "to": quote,
                "rate": Decimal(str(price)),
                "raw": d,
            })

        return results

    except Exception as e:
        logger.error(f"Failed to fetch bulk FX quotes: {e}")
        return []
