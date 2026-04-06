from urllib.parse import urlencode

from django.conf import settings

from apps.integrations.exceptions import ProviderUnavailable
from apps.integrations.providers.fmp.constants import (
    FMP_BASE_URL,
    FMP_MAX_RETRIES,
    FMP_RETRY_BACKOFF_SECONDS,
    FMP_TIMEOUT_SECONDS,
)
from apps.integrations.shared.http import get_json


def api_key_or_raise() -> str:
    api_key = getattr(settings, "FMP_API_KEY", "")
    if not api_key:
        raise ProviderUnavailable("FMP_API_KEY is not configured.")
    return api_key


def build_fmp_url(path: str, **params) -> str:
    cleaned = {key: value for key, value in params.items() if value is not None}
    cleaned["apikey"] = api_key_or_raise()
    base_url = getattr(settings, "FMP_BASE_URL", FMP_BASE_URL)
    return f"{base_url}{path}?{urlencode(cleaned)}"


def fmp_get_json(path: str, **params):
    return get_json(
        build_fmp_url(path, **params),
        timeout=getattr(settings, "INTEGRATIONS_TIMEOUT_SECONDS", FMP_TIMEOUT_SECONDS),
        max_retries=getattr(settings, "INTEGRATIONS_MAX_RETRIES", FMP_MAX_RETRIES),
        backoff_seconds=getattr(
            settings,
            "INTEGRATIONS_RETRY_BACKOFF_SECONDS",
            FMP_RETRY_BACKOFF_SECONDS,
        ),
    )
