from external_data.exceptions import ExternalDataEmptyResult, ExternalDataInvalidResponse
from external_data.providers.fmp.constants import CRYPTO_BATCH_QUOTES, CRYPTO_LIST, QUOTE_SHORT
from external_data.providers.fmp.request import fmp_get_json


def fetch_crypto_list() -> list[dict]:
    data = fmp_get_json(CRYPTO_LIST)
    if not isinstance(data, list):
        raise ExternalDataInvalidResponse("Invalid crypto list response.")
    return data


def fetch_crypto_quote_short(pair_symbol: str) -> dict:
    pair_symbol = (pair_symbol or "").strip().upper()
    if not pair_symbol:
        raise ExternalDataInvalidResponse("Pair symbol is required for crypto quote.")

    data = fmp_get_json(QUOTE_SHORT, symbol=pair_symbol)
    if not isinstance(data, list) or not data:
        raise ExternalDataEmptyResult(f"No crypto quote for {pair_symbol}.")

    row = data[0]
    if not isinstance(row, dict):
        raise ExternalDataInvalidResponse(f"Malformed crypto quote payload for {pair_symbol}.")
    return row


def fetch_crypto_quotes_batch(short: bool = True) -> list[dict]:
    data = fmp_get_json(CRYPTO_BATCH_QUOTES, short=str(short).lower())
    if not isinstance(data, list):
        raise ExternalDataInvalidResponse("Invalid crypto bulk quote response.")
    return data
