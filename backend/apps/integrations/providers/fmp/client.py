from apps.integrations.providers.fmp.provider import FMPProvider
from apps.integrations.shared.provider_guard import ProviderGuard


FMP_PROVIDER = ProviderGuard(name="FMP", provider=FMPProvider())
