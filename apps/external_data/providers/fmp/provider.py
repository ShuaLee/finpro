from typing import Iterable, List

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
    fetch_actively_trading_equity_symbols,
)
from external_data.providers.fmp.equities.classifications.fetchers import (
    fetch_available_sectors,
    fetch_available_industries,
    fetch_available_exchanges,
)
from external_data.providers.fmp.fx.fetchers import (
    fetch_fx_quote,
    fetch_available_countries,
)


class FMPProvider(ExternalDataProvider):
    name = "FMP"

    # --------------------------------------------------
    # Equity profile (metadata only)
    # --------------------------------------------------

    def get_equity_profile(self, symbol: str) -> dict:
        """
        Fetch normalized equity profile data from FMP.

        Used for:
        - Profile sync
        - Sector / industry updates
        - Country / currency resolution
        """
        symbol = symbol.strip().upper()

        data = fetch_equity_profile(symbol)

        profile = data.get("profile")
        if not profile:
            raise ExternalDataEmptyResult(f"No profile data for {symbol}")

        return profile

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

    def get_equity_quotes_bulk(
        self,
        symbols: Iterable[str],
    ) -> List[QuoteSnapshot]:
        """
        Fallback bulk implementation using single-quote endpoint.

        NOTE:
        - This is intentionally inefficient
        - It satisfies the provider contract
        - Can be upgraded to batch endpoint later
        """
        results: list[QuoteSnapshot] = []

        for symbol in symbols:
            try:
                quote = self.get_equity_quote(symbol)
            except ExternalDataEmptyResult:
                continue
            results.append(quote)

        return results

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

    def get_available_countries(self) -> list[str]:
        """
        Return ISO-3166 alpha-2 country codes where equities trade.
        Names are resolved externally (ISO standard).
        """
        return fetch_available_countries() or []

    # --------------------------------------------------
    # Universes / discovery
    # --------------------------------------------------

    def get_actively_traded_equities(self) -> list[dict]:
        """
        Return actively traded equities from FMP.

        Minimal discovery payload:
        - symbol
        - name (may be None)
        """
        symbols = fetch_actively_trading_equity_symbols()

        return [
            {
                "symbol": symbol,
                "name": None,  # profile sync will populate later
            }
            for symbol in symbols
        ]

    # --------------------------------------------------
    # Reference metadata
    # --------------------------------------------------

    def get_available_sectors(self) -> list[str]:
        """
        Return available equity sectors from FMP.
        """
        return fetch_available_sectors() or []

    def get_available_industries(self) -> list[str]:
        """
        Return available equity industries from FMP.
        """
        return fetch_available_industries() or []

    def get_available_exchanges(self) -> list[dict]:
        """
        Return available exchanges from FMP.
        """
        return fetch_available_exchanges() or []
