import requests

from external_data.exceptions import (
    ExternalDataInvalidResponse,
    ExternalDataProviderUnavailable,
    ExternalDataRateLimited,
)

DEFAULT_TIMEOUT = 10


def get_json(url: str, timeout: int = DEFAULT_TIMEOUT):
    """
    Perform a GET request and return parsed JSON.

    Guarantees:
    - Returns parsed JSON (list or dict)
    - OR raises a well-defined ExternalDataError subclass
    - Never returns raw requests.Response

    NOTE:
    - This function is provider-agnostic.
    - Circuit breakers / retries must be applied by the caller.
    """
    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        raise ExternalDataProviderUnavailable(
            "Network error while contacting provider."
        ) from exc

    status = response.status_code

    # --- Rate limiting ---
    if status == 429:
        raise ExternalDataRateLimited(
            "Provider rate limit exceeded (429)"
        )

    # --- Provider outage ---
    if status >= 500:
        raise ExternalDataProviderUnavailable(
            f"Provider server error ({status})"
        )

    # --- Client errors ---
    if status >= 400:
        raise ExternalDataInvalidResponse(
            f"Unexpected client error ({status})"
        )

    # --- Parse JSON ---
    try:
        data = response.json()
    except ValueError as exc:
        raise ExternalDataInvalidResponse(
            "Response contained invalid JSON"
        ) from exc

    if data is None:
        raise ExternalDataInvalidResponse(
            "Provider returned empty response body"
        )

    return data
