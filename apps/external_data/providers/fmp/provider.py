from external_data.providers.base import ExternalDataProvider
from external_data.shared.types import (
    EquityIdentity,
    EquityIdentifierBundle,
    QuoteSnapshot,
    SymbolCandidate,
    FXQuote,
)
from external_data.exceptions import ExternalDataEmptyResult

from external_data.providers.fmp.equities.fetchers import (
    fetch_equity_profile,
    fetch_equity_quote_short,
    fetch_equity_dividends,
)
from external_data.providers.fmp.fx.fetchers import (
    fetch_fx_quote,
)


class FMPProvider(ExternalDataProvider):
    name = "FMP"

    # --------------------------------------------------
    # Equity identity
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Quotes
    # --------------------------------------------------

    def get_equity_quote(self, symbol: str) -> QuoteSnapshot:
        quote = fetch_equity_quote_short(symbol)

        return QuoteSnapshot(
            price=quote.get("price"),
            change=quote.get("change"),
            volume=quote.get("volume"),
        )

    def get_equity_quotes_bulk(self, symbols):
        results = []
        for symbol in symbols:
            try:
                results.append(self.get_equity_quote(symbol))
            except ExternalDataEmptyResult:
                continue
        return results

    # --------------------------------------------------
    # Dividends
    # --------------------------------------------------

    def get_equity_dividends(self, symbol: str) -> list[dict]:
        return fetch_equity_dividends(symbol)

    # --------------------------------------------------
    # Symbol resolution
    # --------------------------------------------------

    def resolve_symbol(self, query: str) -> list[SymbolCandidate]:
        """
        Attempt to resolve renamed or changed equity symbols.

        Strategy:
        - Attempt profile lookup
        - If profile exists but ticker differs → rename detected
        - Otherwise return empty list
        """
        try:
            data = fetch_equity_profile(query)
        except ExternalDataEmptyResult:
            return []

        raw_ids = data.get("identifiers", {})
        symbol = raw_ids.get("TICKER")

        if not symbol:
            return []

        return [
            SymbolCandidate(
                symbol=symbol,
                name=data.get("profile", {}).get("name"),
                exchange=data.get("profile", {}).get("exchange"),
                currency=data.get("profile", {}).get("currency"),
            )
        ]

    # --------------------------------------------------
    # FX
    # --------------------------------------------------

    def get_fx_quote(self, base: str, quote: str) -> FXQuote:
        symbol = f"{base}{quote}"
        data = fetch_fx_quote(symbol)

        return FXQuote(
            base=base,
            quote=quote,
            rate=data["rate"],
        )
