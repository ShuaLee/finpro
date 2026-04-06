import time
from typing import Any

import requests

from apps.integrations.exceptions import (
    InvalidProviderResponse,
    ProviderAccessDenied,
    ProviderRateLimited,
    ProviderUnauthorized,
    ProviderUnavailable,
)


DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_MAX_RETRIES = 2
DEFAULT_BACKOFF_SECONDS = 0.5


def get_json(
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
) -> Any:
    attempt = 0
    while True:
        try:
            response = requests.get(url, timeout=timeout)
        except requests.RequestException as exc:
            if attempt >= max_retries:
                raise ProviderUnavailable("Network error while contacting provider.") from exc
            _sleep_backoff(attempt, backoff_seconds)
            attempt += 1
            continue

        status = response.status_code
        if status == 401:
            raise ProviderUnauthorized("Provider authentication failed (401).")
        if status == 403:
            raise ProviderAccessDenied("Provider denied access to endpoint (403).")
        if status == 429:
            if attempt >= max_retries:
                raise ProviderRateLimited("Provider rate limit exceeded (429).")
            retry_after = _parse_retry_after_seconds(response.headers.get("Retry-After"))
            time.sleep(retry_after if retry_after is not None else _backoff_for_attempt(attempt, backoff_seconds))
            attempt += 1
            continue
        if status >= 500:
            if attempt >= max_retries:
                raise ProviderUnavailable(f"Provider server error ({status}).")
            _sleep_backoff(attempt, backoff_seconds)
            attempt += 1
            continue
        if status >= 400:
            raise InvalidProviderResponse(f"Unexpected client error ({status}).")

        try:
            data = response.json()
        except ValueError as exc:
            raise InvalidProviderResponse("Response contained invalid JSON.") from exc

        if data is None:
            raise InvalidProviderResponse("Provider returned empty response body.")
        return data


def _sleep_backoff(attempt: int, backoff_seconds: float) -> None:
    time.sleep(_backoff_for_attempt(attempt, backoff_seconds))


def _backoff_for_attempt(attempt: int, backoff_seconds: float) -> float:
    return max(backoff_seconds, 0) * (2 ** attempt)


def _parse_retry_after_seconds(value: str | None) -> int | None:
    if not value:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if parsed >= 0 else None
