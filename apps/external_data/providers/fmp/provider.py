from external_data.providers.base import ExternalDataProvider
from external_data.shared.types import (
    EquityIdentity,
    EquityIdentifierBundle,
    QuoteSnapshot,
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

    # --------------------------------------------------
    # Dividends
    # --------------------------------------------------

    def get_equity_dividends(self, symbol: str) -> list[dict]:
        return fetch_equity_dividends(symbol)


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
