from external_data.shared.provider_guard import ProviderGuard
from external_data.providers.fmp.provider import FMPProvider
"""
Financial Modeling Prep (FMP) provider client.

This module defines provider-level identity and lifecycle state.
All FMP requests MUST be executed through FMP_PROVIDER to ensure
circuit-breaking and failure isolation.
"""

FMP_PROVIDER = ProviderGuard(
    name="FMP",
    provider=FMPProvider(),
)
