import logging
import requests

from django.conf import settings

logger = logging.getLogger(__name__)

FMP_BASE = "https://financialmodelingprep.com/stable"
API_KEY = settings.FMP_API_KEY


def fetch_available_exchanges() -> list[dict]:
    """
    Fetch the list of available exchanges from FMP.

    Returns a list of dicts like:
    {
        "exchange": "NASDAQ",
        "name": "NASDAQ",
        "countryName": "United States of America",
        "countryCode": "US",
        "symbolSuffix": "N/A",
        "delay": "Real-time"
    }

    Normalization is handled by the seeder, not here.
    """
    url = f"{FMP_BASE}/available-exchanges?apikey={API_KEY}"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        # Ensure it's a list
        if not isinstance(data, list):
            logger.error("Unexpected exchange response format.")
            return []

        # Ensure records are dictionaries with required keys
        cleaned = []
        for d in data:
            if not isinstance(d, dict):
                continue
            if "exchange" not in d or "name" not in d:
                continue
            cleaned.append(d)

        return cleaned

    except Exception as e:
        logger.error(f"Failed fetching exchanges: {e}")
        return []
