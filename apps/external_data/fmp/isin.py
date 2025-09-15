import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE = "https://financialmodelingprep.com/api/v4"


def fetch_by_isin(isin: str) -> dict | None:
    """
    Fallback reconciliation: fetch security data by ISIN.
    Returns latest ticker + company name + identifiers.
    """
    url = f"{FMP_BASE}/search/isin?isin={isin}&apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data[0] if data else None
    except Exception as e:
        logger.warning(f"ISIN lookup failed for {isin}: {e}")
        return None
