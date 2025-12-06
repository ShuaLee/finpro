import logging

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
    Fetch both profile + quote for a given asset type (by slug).
    Returns a dict that can be merged into Detail models.
    """

    try:
        # ---------------- EQUITY ----------------
        if asset_type == "equity":
            profile = fetch_equity_profile(symbol) or {}
            quote = fetch_equity_quote(symbol) or {}
            return {**profile, **quote} if (profile or quote) else None

        # ---------------- CRYPTO ----------------
        elif asset_type == "crypto":
            profile = fetch_crypto_profile(symbol) or {}
            quote = fetch_crypto_quote(symbol) or {}
            return {**profile, **quote} if (profile or quote) else None

        # ---------------- METAL ----------------
        elif asset_type == "metal":
            return fetch_metal_quote(symbol)

        # ---------------- BOND ----------------
        elif asset_type == "bond":
            profile = fetch_bond_profile(symbol) or {}
            quote = fetch_bond_quote(symbol) or {}
            return {**profile, **quote} if (profile or quote) else None

        # ---------------- UNSUPPORTED ----------------
        else:
            logger.warning(f"Unsupported asset type slug: {asset_type}")
            return None

    except Exception as e:
        logger.error(
            f"Failed to fetch data for {asset_type} {symbol}: {e}",
            exc_info=True,
        )
        return None


# ------------------------------
# Bulk fetch wrapper
# ------------------------------
def bulk_fetch_asset_quotes(symbols: list[str], asset_type: str) -> dict[str, dict]:
    """
    Bulk fetch quotes for multiple symbols of a given asset-type slug.
    Returns {symbol: normalized_data}.
    """

    try:
        # ---------------- EQUITY ----------------
        if asset_type == "equity":
            return fetch_equity_quotes_bulk(symbols)

        # ---------------- CRYPTO ----------------
        elif asset_type == "crypto":
            return bulk_fetch_crypto_quotes(symbols)

        # ---------------- METAL ----------------
        elif asset_type == "metal":
            return bulk_fetch_metal_quotes(symbols)

        # ---------------- BOND ----------------
        elif asset_type == "bond":
            return bulk_fetch_bond_quotes(symbols)

        # ---------------- UNSUPPORTED ----------------
        else:
            logger.warning(
                f"Unsupported asset type slug for bulk fetch: {asset_type}")
            return {}

    except Exception as e:
        logger.error(
            f"Bulk fetch failed for {asset_type} symbols {symbols}: {e}",
            exc_info=True,
        )
        return {}
