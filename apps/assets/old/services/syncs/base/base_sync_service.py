import logging

from external_data.shared.http import ExternalDataProviderUnavailable

logger = logging.getLogger(__name__)


class BaseSyncService:
    """
    Base class for all sync services.
    Handles:
    - FMP outages
    - logging
    - safe execution wrapper
    """

    def safe_run(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ExternalDataProviderUnavailable:
            logger.warning(f"[SYNC] Provider unavailable for {fn.__name__}")
            return None
