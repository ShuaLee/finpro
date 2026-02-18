from external_data.exceptions import ExternalDataEmptyResult, ExternalDataInvalidResponse
from external_data.providers.fmp.constants import COMMODITIES_LIST, COMMODITIES_QUOTE_SHORT
from external_data.providers.fmp.request import fmp_get_json


def fetch_commodity_list() -> list[dict]:
    data = fmp_get_json(COMMODITIES_LIST)
    if not isinstance(data, list):
        raise ExternalDataInvalidResponse("Invalid commodity list response.")
    return data


def fetch_commodity_quote_short(symbol: str) -> dict:
    symbol = (symbol or "").strip().upper()
    if not symbol:
        raise ExternalDataInvalidResponse("Symbol is required for commodity quote.")

    data = fmp_get_json(COMMODITIES_QUOTE_SHORT, symbol=symbol)
    if not isinstance(data, list) or not data:
        raise ExternalDataEmptyResult(f"No commodity quote for {symbol}.")

    row = data[0]
    if not isinstance(row, dict):
        raise ExternalDataInvalidResponse(f"Malformed commodity quote payload for {symbol}.")
    return row
