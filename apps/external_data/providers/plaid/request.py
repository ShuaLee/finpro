import time
from typing import Any

import requests

from external_data.exceptions import (
    ExternalDataAccessDenied,
    ExternalDataInvalidResponse,
    ExternalDataProviderUnavailable,
    ExternalDataRateLimited,
    ExternalDataUnauthorized,
)
from external_data.providers.plaid.constants import (
    PLAID_MAX_RETRIES,
    PLAID_RETRY_BACKOFF_SECONDS,
    PLAID_TIMEOUT_SECONDS,
)


def post_json(
    url: str,
    payload: dict[str, Any],
    *,
    timeout: int = PLAID_TIMEOUT_SECONDS,
    max_retries: int = PLAID_MAX_RETRIES,
    backoff_seconds: float = PLAID_RETRY_BACKOFF_SECONDS,
) -> Any:
    attempt = 0
    while True:
        try:
            response = requests.post(url, json=payload, timeout=timeout)
        except requests.RequestException as exc:
            if attempt >= max_retries:
                raise ExternalDataProviderUnavailable(
                    "Network error while contacting Plaid."
                ) from exc
            _sleep_backoff(attempt, backoff_seconds)
            attempt += 1
            continue

        status = response.status_code

        if status == 401:
            raise ExternalDataUnauthorized("Plaid authentication failed (401).")
        if status == 403:
            raise ExternalDataAccessDenied("Plaid access denied (403).")
        if status == 429:
            if attempt >= max_retries:
                raise ExternalDataRateLimited("Plaid rate limit exceeded (429).")
            _sleep_backoff(attempt, backoff_seconds)
            attempt += 1
            continue
        if status >= 500:
            if attempt >= max_retries:
                raise ExternalDataProviderUnavailable(f"Plaid server error ({status}).")
            _sleep_backoff(attempt, backoff_seconds)
            attempt += 1
            continue
        if status >= 400:
            try:
                body = response.json()
            except ValueError:
                body = response.text
            raise ExternalDataInvalidResponse(f"Plaid client error ({status}): {body}")

        try:
            data = response.json()
        except ValueError as exc:
            raise ExternalDataInvalidResponse("Plaid returned invalid JSON.") from exc

        if not isinstance(data, dict):
            raise ExternalDataInvalidResponse("Plaid returned non-object response.")

        if data.get("error_code"):
            code = data.get("error_code")
            message = data.get("error_message") or "Plaid API error."
            if code in {"INVALID_ACCESS_TOKEN", "INVALID_PUBLIC_TOKEN"}:
                raise ExternalDataUnauthorized(message)
            raise ExternalDataInvalidResponse(message)

        return data


def _sleep_backoff(attempt: int, backoff_seconds: float) -> None:
    time.sleep(max(backoff_seconds, 0) * (2 ** attempt))

