import logging

from core.types import DomainType

# Import fetchers
from external_data.fmp.equities.fetchers import (
    fetch_equity_profile,
    fetch_equity_quote,
    fetch_equity_quotes_bulk,
)
from apps.external_data.fmp.crypto.fetchers import (
    fetch_crypto_profile,
    fetch_crypto_quote,
    bulk_fetch_crypto_quotes,
)
from external_data.fmp.metals.fetchers import (
    fetch_metal_quote,
    bulk_fetch_metal_quotes,
)
from external_data.fmp.bonds.fetchers import (
    fetch_bond_profile,
    fetch_bond_quote,
    bulk_fetch_bond_quotes,
)

logger = logging.getLogger(__name__)


# ------------------------------
# Single fetch wrapper
# ------------------------------
def fetch_asset_data(symbol: str, asset_type: str) -> dict | None:
    """
    Fetch both profile + quote for a given asset type.
    Returns a dict that can be merged into Detail models.
    """
    try:
        if asset_type == DomainType.EQUITY:
            profile = fetch_equity_profile(symbol) or {}
            quote = fetch_equity_quote(symbol) or {}
            return {**profile, **quote} if profile or quote else None

        elif asset_type == DomainType.CRYPTO:
            profile = fetch_crypto_profile(symbol) or {}
            quote = fetch_crypto_quote(symbol) or {}
            return {**profile, **quote} if profile or quote else None

        elif asset_type == DomainType.METAL:
            return fetch_metal_quote(symbol)

        elif asset_type == DomainType.BOND:
            profile = fetch_bond_profile(symbol) or {}
            quote = fetch_bond_quote(symbol) or {}
            return {**profile, **quote} if profile or quote else None

        else:
            logger.warning(f"Unsupported asset type: {asset_type}")
            return None

    except Exception as e:
        logger.error(
            f"Failed to fetch {asset_type} {symbol}: {e}", exc_info=True)
        return None


# ------------------------------
# Bulk fetch wrapper
# ------------------------------
def bulk_fetch_asset_quotes(symbols: list[str], asset_type: str) -> dict[str, dict]:
    """
    Bulk fetch quotes for multiple symbols of a given type.
    Returns {symbol: normalized_data}.
    """
    try:
        if asset_type == DomainType.EQUITY:
            return fetch_equity_quotes_bulk(symbols)
        elif asset_type == DomainType.CRYPTO:
            return bulk_fetch_crypto_quotes(symbols)
        elif asset_type == DomainType.METAL:
            return bulk_fetch_metal_quotes(symbols)
        elif asset_type == DomainType.BOND:
            return bulk_fetch_bond_quotes(symbols)
        else:
            logger.warning(
                f"Unsupported asset type for bulk fetch: {asset_type}")
            return {}
    except Exception as e:
        logger.error(
            f"Bulk fetch failed for {asset_type} symbols {symbols}: {e}", exc_info=True)
        return {}
