from external_data.exceptions import ExternalDataEmptyResult
from external_data.providers.fmp.constants import (
    FMP_BASE_URL,
    FMP_API_KEY,
    COMMODITIES_LIST,
    COMMODITIES_QUOTE_SHORT
)
from external_data.shared.http import get_json


def fetch_commodity_list() -> list[dict]:
    """
    Fetch the full commodity universe from FMP.
    """
    url = f"{FMP_BASE_URL}{COMMODITIES_LIST}?apikey={FMP_API_KEY}"
    return get_json(url) or []


def fetch_commodity_quote_short(symbol: str) -> dict:
    """
    Fetch a fast quote for a single commodity.
    """
    url = f"{FMP_BASE_URL}{COMMODITIES_QUOTE_SHORT}?symbol={symbol}&apikey={FMP_API_KEY}"
    data = get_json(url)

    if not data:
        raise ExternalDataEmptyResult(f"No commodity quote for {symbol}")

    return data[0]