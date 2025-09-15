import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE = "https://financialmodelingprep.com/api/v3"


def fetch_stock_universe() -> list[dict]:
    """
    Fetch the full universe of stocks from FMP.
    Used for initial DB seeding and occasional full refresh.
    """
    url = f"{FMP_BASE}/stock/list?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json() or []
    except Exception as e:
        logger.error(f"Failed to fetch stock universe: {e}")
        return []
