import logging
import requests

from django.conf import settings

logger = logging.getLogger(__name__)


FMP_BASE = "https://financialmodelingprep.com/stable"
API_KEY = settings.FMP_API_KEY


def fetch_available_sectors() -> list[str]:
    url = f"{FMP_BASE}/available-sectors?apikey={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        return [d["sector"] for d in data if "sector" in d]
    except Exception as e:
        logger.error(f"Failed fetching sectors: {e}")
        return []


def fetch_available_industries() -> list[str]:
    url = f"{FMP_BASE}/available-industries?apikey={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        return [d["industry"] for d in data if "industry" in d]
    except Exception as e:
        logger.error(f"failed fetching industries: {e}")
        return []
