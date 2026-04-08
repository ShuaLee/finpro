from apps.integrations.exceptions import EmptyProviderResult, InvalidProviderResponse
from apps.integrations.providers.fmp.constants import (
    ACTIVELY_TRADING_LIST,
    AVAILABLE_COUNTRIES,
    COMMODITIES_LIST,
    CRYPTOCURRENCY_LIST,
    DIVIDENDS,
    FOREX_LIST,
    PROFILE,
    PROFILE_CIK,
    PROVIDER_NAME,
    QUOTE_SHORT,
    SEARCH_CUSIP,
    SEARCH_ISIN,
    STOCK_LIST,
)
from apps.integrations.providers.fmp.parsers import (
    parse_actively_traded_row,
    parse_active_equity_row,
    parse_company_profile_payload,
    parse_commodity_list_row,
    parse_crypto_list_row,
    parse_identifier_search_row,
    parse_profile_identity_payload,
    parse_quote_payload,
    parse_stock_list_row,
)
from apps.integrations.providers.fmp.request import fmp_get_json
from apps.integrations.providers.market_data import MarketDataProvider
from apps.integrations.shared.types import CompanyProfile, QuoteSnapshot


class FMPProvider(MarketDataProvider):
    name = PROVIDER_NAME

    def get_quote(self, symbol: str) -> QuoteSnapshot:
        normalized = (symbol or "").strip().upper()
        if not normalized:
            raise InvalidProviderResponse("Symbol is required for quote lookup.")

        data = fmp_get_json(QUOTE_SHORT, symbol=normalized)
        if not isinstance(data, list) or not data:
            raise EmptyProviderResult(f"No quote found for {normalized}.")
        row = data[0]
        if not isinstance(row, dict):
            raise InvalidProviderResponse(f"Malformed quote payload for {normalized}.")
        return parse_quote_payload(row, source=self.name)

    def get_company_profile(self, symbol: str) -> CompanyProfile:
        normalized = (symbol or "").strip().upper()
        if not normalized:
            raise InvalidProviderResponse("Symbol is required for profile lookup.")

        data = fmp_get_json(PROFILE, symbol=normalized)
        if not isinstance(data, list) or not data:
            raise EmptyProviderResult(f"No profile found for {normalized}.")
        row = data[0]
        if not isinstance(row, dict):
            raise InvalidProviderResponse(f"Malformed profile payload for {normalized}.")
        return parse_company_profile_payload(row)

    def get_dividends(self, symbol: str) -> list[dict]:
        normalized = (symbol or "").strip().upper()
        if not normalized:
            raise InvalidProviderResponse("Symbol is required for dividend lookup.")

        data = fmp_get_json(DIVIDENDS, symbol=normalized)
        if not isinstance(data, list):
            return []
        return [row for row in data if isinstance(row, dict)]

    def get_forex_list(self) -> list[dict]:
        data = fmp_get_json(FOREX_LIST)
        if not isinstance(data, list):
            raise InvalidProviderResponse("Malformed forex list payload.")
        return [row for row in data if isinstance(row, dict)]

    def get_available_countries(self) -> list[str]:
        data = fmp_get_json(AVAILABLE_COUNTRIES)
        if not isinstance(data, list):
            raise InvalidProviderResponse("Malformed available countries payload.")
        results: list[str] = []
        for row in data:
            if not isinstance(row, dict):
                continue
            code = (row.get("country") or "").strip().upper()
            if code:
                results.append(code)
        return results

    def get_stock_list(self) -> list[dict]:
        data = fmp_get_json(STOCK_LIST)
        if not isinstance(data, list):
            raise InvalidProviderResponse("Malformed stock list payload.")

        parsed: list[dict] = []
        for row in data:
            if not isinstance(row, dict):
                continue
            try:
                parsed.append(parse_stock_list_row(row))
            except InvalidProviderResponse:
                continue
        return parsed

    def get_actively_traded_symbols(self) -> set[str]:
        data = fmp_get_json(ACTIVELY_TRADING_LIST)
        if not isinstance(data, list):
            raise InvalidProviderResponse("Malformed actively trading list payload.")

        parsed: set[str] = set()
        for row in data:
            if not isinstance(row, dict):
                continue
            try:
                parsed.add(parse_actively_traded_row(row))
            except InvalidProviderResponse:
                continue
        return parsed

    def get_actively_traded_rows(self) -> list[dict]:
        data = fmp_get_json(ACTIVELY_TRADING_LIST)
        if not isinstance(data, list):
            raise InvalidProviderResponse("Malformed actively trading list payload.")

        parsed: list[dict] = []
        for row in data:
            if not isinstance(row, dict):
                continue
            try:
                parsed.append(parse_active_equity_row(row))
            except InvalidProviderResponse:
                continue
        return parsed

    def get_profile_with_identifiers(self, symbol: str) -> dict:
        normalized = (symbol or "").strip().upper()
        if not normalized:
            raise InvalidProviderResponse("Symbol is required for profile lookup.")

        data = fmp_get_json(PROFILE, symbol=normalized)
        if not isinstance(data, list) or not data:
            raise EmptyProviderResult(f"No profile found for {normalized}.")
        row = data[0]
        if not isinstance(row, dict):
            raise InvalidProviderResponse(f"Malformed profile payload for {normalized}.")
        return parse_profile_identity_payload(row)

    def get_cryptocurrency_rows(self) -> list[dict]:
        data = fmp_get_json(CRYPTOCURRENCY_LIST)
        if not isinstance(data, list):
            raise InvalidProviderResponse("Malformed cryptocurrency list payload.")

        parsed: list[dict] = []
        for row in data:
            if not isinstance(row, dict):
                continue
            try:
                parsed.append(parse_crypto_list_row(row))
            except InvalidProviderResponse:
                continue
        return parsed

    def get_commodity_rows(self) -> list[dict]:
        data = fmp_get_json(COMMODITIES_LIST)
        if not isinstance(data, list):
            raise InvalidProviderResponse("Malformed commodities list payload.")

        parsed: list[dict] = []
        for row in data:
            if not isinstance(row, dict):
                continue
            try:
                parsed.append(parse_commodity_list_row(row))
            except InvalidProviderResponse:
                continue
        return parsed

    def search_by_isin(self, isin: str) -> list[dict]:
        normalized = (isin or "").strip().upper()
        if not normalized:
            return []
        data = fmp_get_json(SEARCH_ISIN, isin=normalized)
        if not isinstance(data, list):
            return []
        return [parse_identifier_search_row(row) for row in data if isinstance(row, dict)]

    def search_by_cusip(self, cusip: str) -> list[dict]:
        normalized = (cusip or "").strip().upper()
        if not normalized:
            return []
        data = fmp_get_json(SEARCH_CUSIP, cusip=normalized)
        if not isinstance(data, list):
            return []
        return [parse_identifier_search_row(row) for row in data if isinstance(row, dict)]

    def search_by_cik(self, cik: str) -> list[dict]:
        normalized = (cik or "").strip()
        if not normalized:
            return []
        data = fmp_get_json(PROFILE_CIK, cik=normalized)
        if not isinstance(data, list):
            return []
        return [parse_identifier_search_row(row) for row in data if isinstance(row, dict)]
