import logging
from abc import ABC, abstractmethod
from typing import Any


logger = logging.getLogger(__name__)


class BaseSyncService(ABC):
    """
    Base class for all sync services.

    Responsibilities:
    - Provide a consistent sync interface
    - Centralize logging
    - Act as a hook point for retries, metrics, and scheduling
    """

    name: str | None = None

    def __init__(self, *, force: bool = False):
        self.force = force

    def sync(self, *args, **kwargs) -> Any:
        """
        Public entry point for executing a sync.

        This method should not be overridden.
        Subclasses must implement `_sync()`.
        """
        service_name = self.name or self.__class__.__name__
        logger.debug("Starting sync: %s", service_name)

        try:
            result = self._sync(*args, **kwargs)
        except Exception:
            logger.exception("Sync failed: %s", service_name)
            raise
        else:
            logger.debug("Sync completed: %s", service_name)
            return result

    @abstractmethod
    def _sync(self, *args, **kwargs) -> Any:
        """
        Actual sync implementation.

        Subclasses implement this method.
        """
        raise NotImplementedError
