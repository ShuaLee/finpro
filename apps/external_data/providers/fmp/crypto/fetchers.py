from external_data.exceptions import ExternalDataEmptyResult
from external_data.providers.fmp.constants import (
    FMP_BASE_URL,
    FMP_API_KEY,
    CRYPTO_LIST,
    CRYPTO_BATCH_QUOTES,
    QUOTE_SHORT,
)
from external_data.shared.http import get_json


def fetch_crypto_list() -> list[dict]:
    url = f"{FMP_BASE_URL}{CRYPTO_LIST}?apikey={FMP_API_KEY}"
    return get_json(url) or []


def fetch_crypto_quote_short(pair_symbol: str) -> dict:
    url = f"{FMP_BASE_URL}{QUOTE_SHORT}?symbol={pair_symbol}&apikey={FMP_API_KEY}"
    data = get_json(url)

    if not data:
        raise ExternalDataEmptyResult(f"No crypto quote for {pair_symbol}")

    return data[0]


def fetch_crypto_quotes_batch(short: bool = True) -> list[dict]:
    url = f"{FMP_BASE_URL}{CRYPTO_BATCH_QUOTES}?short={str(short).lower()}&apikey={FMP_API_KEY}"
    return get_json(url) or []
