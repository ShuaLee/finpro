class ExternalDataError(Exception):
    """
    Base exception for all external data-related failures.

    This should NEVER be raised directly.
    It exists so services can safely catch *all* external-data issues
    without accidentally catching unrelated exceptions.
    """
    pass


class ExternalDataProviderUnavailable(ExternalDataError):
    """
    Raised when a provider is unavailable or unhealthy.

    Examples:
    - Network failure
    - Timeout
    - 5xx response
    - Circuit breaker open

    Service behavior:
    - Do NOT persist anything
    - Log provider outage
    - Retry later
    """
    pass


class ExternalDataInvalidResponse(ExternalDataError):
    """
    Raised when a provider responds successfully (2xx),
    but the payload is malformed, unexpected, or violates assumptions.

    Examples:
    - JSON schema changed
    - Expected list but got dict
    - Missing required fields

    Service behavior:
    - Do NOT persist anything
    - Log schema drift / provider bug
    - Do NOT retry aggressively
    """
    pass


class ExternalDataEmptyResult(ExternalDataError):
    """
    Raised when a provider responds successfully,
    but returns no meaningful data.

    Examples:
    - Empty list for a valid symbol
    - No quote returned
    - No profile found

    Service behavior:
    - Safe to ignore or mark asset as inactive
    - NOT a provider outage
    """
    pass


class ExternalDataRateLimited(ExternalDataProviderUnavailable):
    """
    Raised when the provider explicitly rate-limits requests (HTTP 429).

    Subclass of ProviderUnavailable because behavior is the same,
    but allows finer-grained logging and metrics.
    """
    pass


class ExternalDataAccessDenied(ExternalDataError):
    """
    Raised when credentials are valid but endpoint access is forbidden.

    Common causes:
    - Plan does not include the endpoint
    - Region/instrument coverage not included in current tier
    """
    pass


class ExternalDataUnauthorized(ExternalDataError):
    """
    Raised when provider credentials are missing/invalid.
    """
    pass
