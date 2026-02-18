import logging
from typing import Iterable, List

from external_data.exceptions import ExternalDataAccessDenied, ExternalDataEmptyResult
from external_data.providers.base import ExternalDataProvider
from external_data.providers.fmp.commodity.fetchers import (
    fetch_commodity_list,
    fetch_commodity_quote_short,
)
from external_data.providers.fmp.crypto.fetchers import (
    fetch_crypto_list,
    fetch_crypto_quote_short,
    fetch_crypto_quotes_batch,
)
from external_data.providers.fmp.equities.classifications.fetchers import (
    fetch_available_exchanges,
    fetch_available_industries,
    fetch_available_sectors,
)
from external_data.providers.fmp.equities.fetchers import (
    fetch_actively_trading_equity_symbols,
    fetch_equity_dividends,
    fetch_equity_profile,
    fetch_equity_quote_short,
)
from external_data.providers.fmp.fx.fetchers import fetch_available_countries, fetch_fx_quote
from external_data.shared.types import (
    FXQuote,
    EquityIdentifierBundle,
    EquityIdentity,
    QuoteSnapshot,
)

logger = logging.getLogger(__name__)


class FMPProvider(ExternalDataProvider):
    name = "FMP"

    def get_equity_profile(self, symbol: str) -> dict:
        symbol = symbol.strip().upper()
        data = fetch_equity_profile(symbol)
        profile = data.get("profile")
        if not profile:
            raise ExternalDataEmptyResult(f"No profile data for {symbol}")
        return profile

    def get_equity_identity(self, symbol: str) -> EquityIdentity:
        symbol = symbol.strip().upper()
        data = fetch_equity_profile(symbol)
        profile = data["profile"]
        raw_ids = data["identifiers"]
        returned_ticker = raw_ids.get("TICKER")
        if not returned_ticker:
            raise ExternalDataEmptyResult(f"No ticker returned for {symbol}")

        return EquityIdentity(
            symbol=returned_ticker.upper(),
            profile=profile,
            identifiers=EquityIdentifierBundle(
                ticker=returned_ticker,
                isin=raw_ids.get("ISIN"),
                cusip=raw_ids.get("CUSIP"),
                cik=raw_ids.get("CIK"),
            ),
        )

    def get_equity_quote(self, symbol: str) -> QuoteSnapshot:
        quote = fetch_equity_quote_short(symbol)
        return QuoteSnapshot(
            price=quote.get("price"),
            change=quote.get("change"),
            volume=quote.get("volume"),
        )

    def get_equity_quotes_bulk(self, symbols: Iterable[str]) -> List[QuoteSnapshot]:
        results: list[QuoteSnapshot] = []
        for symbol in symbols:
            try:
                quote = self.get_equity_quote(symbol)
            except ExternalDataEmptyResult:
                continue
            results.append(quote)
        return results

    def get_equity_dividends(self, symbol: str) -> list[dict]:
        return fetch_equity_dividends(symbol)

    def get_fx_quote(self, base: str, quote: str) -> FXQuote:
        symbol = f"{base}{quote}"
        data = fetch_fx_quote(symbol)
        return FXQuote(base=base, quote=quote, rate=data["rate"])

    def get_available_countries(self) -> list[str]:
        try:
            return fetch_available_countries() or []
        except ExternalDataAccessDenied:
            logger.warning("FMP plan does not include available countries endpoint.")
            return []

    def get_actively_traded_equities(self) -> list[dict]:
        try:
            symbols = fetch_actively_trading_equity_symbols()
        except ExternalDataAccessDenied:
            logger.warning("FMP plan does not include actively trading list endpoint.")
            return []

        return [{"symbol": symbol, "name": None} for symbol in symbols]

    def get_available_sectors(self) -> list[str]:
        try:
            return fetch_available_sectors() or []
        except ExternalDataAccessDenied:
            logger.warning("FMP plan does not include available sectors endpoint.")
            return []

    def get_available_industries(self) -> list[str]:
        try:
            return fetch_available_industries() or []
        except ExternalDataAccessDenied:
            logger.warning("FMP plan does not include available industries endpoint.")
            return []

    def get_available_exchanges(self) -> list[dict]:
        try:
            return fetch_available_exchanges() or []
        except ExternalDataAccessDenied:
            logger.warning("FMP plan does not include available exchanges endpoint.")
            return []

    def get_cryptocurrencies(self) -> list[dict]:
        try:
            return fetch_crypto_list()
        except ExternalDataAccessDenied:
            logger.warning("FMP plan does not include cryptocurrency list endpoint.")
            return []

    def get_crypto_quote(self, pair_symbol: str):
        return fetch_crypto_quote_short(pair_symbol)

    def get_crypto_quotes_bulk(self):
        try:
            return fetch_crypto_quotes_batch(short=True)
        except ExternalDataAccessDenied:
            logger.warning("FMP plan does not include crypto bulk quote endpoint.")
            return []

    def get_commodities(self) -> list[dict]:
        try:
            return fetch_commodity_list()
        except ExternalDataAccessDenied:
            logger.warning("FMP plan does not include commodities list endpoint.")
            return []

    def get_commodity_quote(self, symbol: str) -> QuoteSnapshot:
        symbol = symbol.strip().upper()
        quote = fetch_commodity_quote_short(symbol)
        return QuoteSnapshot(
            price=quote.get("price"),
            change=quote.get("change"),
            volume=quote.get("volume"),
        )
