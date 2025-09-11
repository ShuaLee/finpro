import logging
from apps.external_data.fmp.equity import fetch_stock_quote, fetch_stock_profile
from external_data.fmp.metals import fetch_precious_metal_quote

logger = logging.getLogger(__name__)


def fetch_asset_data(symbol: str, asset_type: str) -> dict | None:
    """
    Centralized fetcher for any asset type.
    Returns JSON/dict, leaves DB updates to sync services.
    """
    if asset_type == "stock":
        quote = fetch_stock_quote(symbol)
        profile = fetch_stock_profile(symbol)
        if not quote or not profile:
            return None
        return {"quote": quote, "profile": profile}

    elif asset_type == "metal":
        return fetch_precious_metal_quote(symbol)

    else:
        raise NotImplementedError(f"Unsupported asset type: {asset_type}")
