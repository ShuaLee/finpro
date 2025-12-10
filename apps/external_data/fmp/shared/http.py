import logging
import requests


logger = logging.getLogger(__name__)


class ExternalDataProviderUnavailable(Exception):
    """Raised when a provider (FMP, etc.) is down or unresponsive."""
    pass


def _get_json(url: str, timeout=10) -> dict | list | None:
    """
    Shared safe HTTP GET for all external-data APIs.
    Handles:
    - connection errors
    - timeouts
    - provider outages (500-series)
    - returns None on failure
    """
    try:
        r = requests.get(url, timeout=timeout)

        # Explicitly detect provider outage
        if r.status_code >= 500:
            raise ExternalDataProviderUnavailable(
                f"Provider server error ({r.status_code})"
            )

        r.raise_for_status()
        return r.json()

    except ExternalDataProviderUnavailable:
        # Let callers use this to show a user-facing error
        raise

    except Exception as e:
        logger.warning(f"HTTP request failed: {e} — URL: {url}")
        return None
