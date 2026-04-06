import logging
import time
from typing import Any, Callable

from apps.integrations.exceptions import IntegrationError, ProviderUnavailable

logger = logging.getLogger(__name__)


class ProviderGuard:
    MAX_FAILURES = 5
    COOLDOWN_SECONDS = 300

    def __init__(self, *, name: str, provider):
        self.name = name
        self.provider = provider
        self.consecutive_failures = 0
        self.last_success_ts: float | None = None
        self.last_failure_ts: float | None = None

    def __getattr__(self, attr):
        target = getattr(self.provider, attr)
        if not callable(target):
            return target

        def guarded(*args, **kwargs):
            return self.request(target, *args, **kwargs)

        return guarded

    def can_call(self) -> bool:
        if self.consecutive_failures < self.MAX_FAILURES:
            return True
        if not self.last_failure_ts:
            return True
        return (time.time() - self.last_failure_ts) > self.COOLDOWN_SECONDS

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.last_success_ts = time.time()

    def record_failure(self, exc: Exception | None = None) -> None:
        self.consecutive_failures += 1
        self.last_failure_ts = time.time()
        logger.warning("[PROVIDER:%s] failure #%s", self.name, self.consecutive_failures)
        if exc:
            logger.debug("[PROVIDER:%s] exception=%r", self.name, exc)

    def request(self, fn: Callable[..., Any], *args, **kwargs):
        if not self.can_call():
            raise ProviderUnavailable(f"{self.name} is temporarily unavailable (circuit open).")

        try:
            result = fn(*args, **kwargs)
        except ProviderUnavailable as exc:
            self.record_failure(exc)
            raise
        except IntegrationError:
            raise
        except Exception as exc:
            self.record_failure(exc)
            raise ProviderUnavailable(f"{self.name} request failed.") from exc

        self.record_success()
        return result
