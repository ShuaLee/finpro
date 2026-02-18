from external_data.providers.plaid.provider import PlaidProvider
from external_data.shared.provider_guard import ProviderGuard


PLAID_PROVIDER = ProviderGuard(
    name="PLAID",
    provider=PlaidProvider(),
)

