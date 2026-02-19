from urllib.parse import urlencode

from external_data.exceptions import ExternalDataProviderUnavailable
from external_data.providers.fmp.constants import (
    FMP_API_KEY,
    FMP_BASE_URL,
    FMP_MAX_RETRIES,
    FMP_RETRY_BACKOFF_SECONDS,
    FMP_TIMEOUT_SECONDS,
)
from external_data.shared.http import get_json


def api_key_or_raise() -> str:
    if not FMP_API_KEY:
        raise ExternalDataProviderUnavailable("FMP_API_KEY is not configured.")
    return FMP_API_KEY


def build_fmp_url(path: str, **params) -> str:
    cleaned = {k: v for k, v in params.items() if v is not None}
    cleaned["apikey"] = api_key_or_raise()
    return f"{FMP_BASE_URL}{path}?{urlencode(cleaned)}"


def fmp_get_json(path: str, **params):
    return get_json(
        build_fmp_url(path, **params),
        timeout=FMP_TIMEOUT_SECONDS,
        max_retries=FMP_MAX_RETRIES,
        backoff_seconds=FMP_RETRY_BACKOFF_SECONDS,
    )
