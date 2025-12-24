import logging
import time

from typing import Any, Callable

from external_data.exceptions import (
    ExternalDataError,
    ExternalDataProviderUnavailable
)

logger = logging.getLogger(__name__)


class ProviderGuard:
    """
    Lightweight circuit breaker for external data providers.

    Responsibilities:
    - Track consecutive provider-level failures
    - Temporarily block calls after repeated failures
    - Normalize unexpected errors into provider unavailability

    This class does NOT:
    - Retry requests
    - Interpret business meaning
    - Handle HTTP directly
    """

    MAX_FAILURES = 5
    COOLDOWN_SECONDS = 300  # 5 minutes

    def __init__(self, name: str, provider):
        self.name = name
        self.provider = provider
        self.consecutive_failures = 0
        self.last_success_ts: float | None = None
        self.last_failure_ts: float | None = None

    def __getattr__(self, attr):
        """
        Forward provider method calls through the circuit breaker.
        """
        target = getattr(self.provider, attr)

        if not callable(target):
            return target

        def guarded(*args, **kwargs):
            return self.request(target, *args, **kwargs)

        return guarded

    # --------------------------------------------------
    # Circuit breaker state
    # --------------------------------------------------

    def can_call(self) -> bool:
        """
        Determine whether calls to the provider are currently allowed.
        """
        if self.consecutive_failures < self.MAX_FAILURES:
            return True

        if not self.last_failure_ts:
            return True

        # Allow retry after cooldown window
        return (time.time() - self.last_failure_ts) > self.COOLDOWN_SECONDS

    def record_success(self):
        """
        Reset failure state after a successful call.
        """
        self.consecutive_failures = 0
        self.last_success_ts = time.time()

    def record_failure(self, exc: Exception | None = None):
        """
        Record a provider-level failure.
        """
        self.consecutive_failures += 1
        self.last_failure_ts = time.time()

        logger.warning(
            "[PROVIDER:%s] failure #%s",
            self.name,
            self.consecutive_failures,
        )

        if exc:
            logger.debug(
                "[PROVIDER:%s] failure exception: %s",
                self.name,
                repr(exc),
            )

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------
    def request(self, fn: Callable[..., Any], *args, **kwargs):
        """
        Execute a provider call through the circuit breaker.

        Guarantees:
        - If the circuit is open → ExternalDataProviderUnavailable
        - If the call succeeds → result returned, failures reset
        - Provider failures affect circuit state
        - Semantic/data errors propagate unchanged
        """

        if not self.can_call():
            raise ExternalDataProviderUnavailable(
                f"{self.name} is temporarily unavailable (circuit open)"
            )

        try:
            result = fn(*args, **kwargs)

        except ExternalDataProviderUnavailable as exc:
            # Provider-level failure → count it
            self.record_failure(exc)
            raise

        except ExternalDataError:
            # Semantic / data error → DO NOT count, DO NOT wrap
            raise

        except Exception as exc:
            # Truly unexpected error → treat as provider failure
            self.record_failure(exc)
            raise ExternalDataProviderUnavailable(
                f"{self.name} request failed"
            ) from exc

        else:
            self.record_success()
            return result
