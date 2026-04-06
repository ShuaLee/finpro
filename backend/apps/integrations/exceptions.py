class IntegrationError(Exception):
    pass


class ProviderUnavailable(IntegrationError):
    pass


class InvalidProviderResponse(IntegrationError):
    pass


class EmptyProviderResult(IntegrationError):
    pass


class ProviderRateLimited(ProviderUnavailable):
    pass


class ProviderAccessDenied(IntegrationError):
    pass


class ProviderUnauthorized(IntegrationError):
    pass
