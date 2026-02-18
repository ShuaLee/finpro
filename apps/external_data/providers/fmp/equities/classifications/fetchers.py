from external_data.exceptions import ExternalDataInvalidResponse
from external_data.providers.fmp.constants import (
    AVAILABLE_EXCHANGES,
    AVAILABLE_INDUSTRIES,
    AVAILABLE_SECTORS,
)
from external_data.providers.fmp.equities.classifications.parsers import (
    parse_exchange,
    parse_industry,
    parse_sector,
)
from external_data.providers.fmp.request import fmp_get_json


def fetch_available_sectors() -> list[str]:
    data = fmp_get_json(AVAILABLE_SECTORS)
    if not isinstance(data, list):
        raise ExternalDataInvalidResponse("Invalid available-sectors response.")
    return [sector for row in data if (sector := parse_sector(row))]


def fetch_available_industries() -> list[str]:
    data = fmp_get_json(AVAILABLE_INDUSTRIES)
    if not isinstance(data, list):
        raise ExternalDataInvalidResponse("Invalid available-industries response.")
    return [industry for row in data if (industry := parse_industry(row))]


def fetch_available_exchanges() -> list[dict]:
    data = fmp_get_json(AVAILABLE_EXCHANGES)
    if not isinstance(data, list):
        raise ExternalDataInvalidResponse("Invalid available-exchanges response.")

    exchanges: list[dict] = []
    for row in data:
        parsed = parse_exchange(row)
        if parsed:
            exchanges.append(parsed)
    return exchanges
