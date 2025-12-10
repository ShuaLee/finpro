import logging
import requests

from external_data.fmp.shared.constants import FMP_API_KEY, FMP_STABLE

logger = logging.getLogger(__name__)

# --------------------------------------------------------
# Helper: GET JSON safely
# --------------------------------------------------------


def _get_json(url: str) -> dict | list | None:
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning(f"FMP requests failed: {e} - URL: {url}")
        return None
