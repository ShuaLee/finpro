import logging
from apps.external_data.fmp.equity import fetch_equity_quote, fetch_equity_profile
from apps.external_data.fmp.bonds import fetch_bond_profile, fetch_bond_quote
from apps.external_data.fmp.crypto import fetch_crypto_profile, fetch_crypto_quote
from apps.external_data.fmp.metals import fetch_metal_quote
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"


def fetch_asset_data(symbol: str, asset_type: str) -> dict | None:
    """
    Centralized fetcher for any asset type.
    Returns JSON/dict, leaves DB updates to sync services.
    """
    if asset_type == "equity":
        quote = fetch_equity_quote(symbol)
        profile = fetch_equity_profile(symbol)
        if not quote or not profile:
            return None
        return {"quote": quote, "profile": profile}

    elif asset_type == "bond":
        quote = fetch_bond_quote(symbol)
        profile = fetch_bond_profile(symbol)
        if not quote or not profile:
            return None
        return {"quote": quote, "profile": profile}

    elif asset_type == "crypto":
        quote = fetch_crypto_quote(symbol)
        profile = fetch_crypto_profile(symbol)
        if not quote or not profile:
            return None
        return {"quote": quote, "profile": profile}

    elif asset_type == "metal":
        return fetch_metal_quote(symbol)

    elif asset_type in {"real_estate", "custom"}:
        # User-entered assets, no external sync
        return None

    else:
        raise NotImplementedError(f"Unsupported asset type: {asset_type}")



def detect_asset_type(symbol: str) -> str | None:
    """
    Detect the asset type of a symbol.
    Priority:
      1. FMP /search (cheap + fast)
      2. Fallback to direct profile/quote fetchers
    """
    # --- 1. Try /search ---
    try:
        url = f"{FMP_BASE_URL}/search?query={symbol}&limit=1&apikey={FMP_API_KEY}"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if data:
            raw_type = data[0].get("type", "").lower()
            if raw_type in {"stock", "etf", "mutual fund", "fund"}:
                return "equity"
            if raw_type in {"crypto", "cryptocurrency"}:
                return "crypto"
            if raw_type in {"bond"}:
                return "bond"
            if raw_type in {"commodity", "metal"}:
                return "metal"
    except Exception as e:
        logger.warning(f"Search detection failed for {symbol}: {e}")

    # --- 2. Fallbacks ---
    if fetch_equity_profile(symbol):
        return "equity"
    if fetch_bond_profile(symbol):
        return "bond"
    if fetch_crypto_profile(symbol):
        return "crypto"
    if fetch_metal_quote(symbol):
        return "metal"

    return None