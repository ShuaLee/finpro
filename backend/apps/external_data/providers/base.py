from abc import ABC, abstractmethod
from typing import Iterable, List

from external_data.shared.types import (
    EquityIdentity,
    QuoteSnapshot,
    FXQuote,
)


class ExternalDataProvider(ABC):
    """
    Abstract base class for all external market data providers.

    This defines the contract that service layers rely on.
    Implementations (FMP, others) must:
    - Return shared types
    - Raise ExternalDataError subclasses on failure
    """

    name: str

    # --------------------------------------------------
    # Equity identity & metadata
    # --------------------------------------------------

    @abstractmethod
    def get_equity_identity(self, symbol: str) -> EquityIdentity:
        """
        Resolve and return an equity identity by symbol.

        Must raise:
        - ExternalDataEmptyResult if symbol does not exist
        - ExternalDataProviderUnavailable if provider is down
        - ExternalDataInvalidResponse on schema issues
        """
        raise NotImplementedError

    # --------------------------------------------------
    # Quotes
    # --------------------------------------------------

    @abstractmethod
    def get_equity_quote(self, symbol: str) -> QuoteSnapshot:
        """
        Fetch a fast-moving equity quote.

        Must raise:
        - ExternalDataEmptyResult if symbol does not exist
        - ExternalDataProviderUnavailable if provider is down
        """
        raise NotImplementedError

    @abstractmethod
    def get_equity_quotes_bulk(self, symbols: Iterable[str]) -> List[QuoteSnapshot]:
        """
        Fetch quotes for many equities at once.

        Implementations may drop invalid symbols silently
        but must not return malformed quote objects.
        """
        raise NotImplementedError

    # --------------------------------------------------
    # Dividends
    # --------------------------------------------------

    @abstractmethod
    def get_equity_dividends(self, symbol: str) -> list[dict]:
        """
        Fetch historical dividend events for an equity.

        Empty list is valid (non-dividend-paying equity).
        """
        raise NotImplementedError

    # --------------------------------------------------
    # FX
    # --------------------------------------------------

    @abstractmethod
    def get_fx_quote(self, base: str, quote: str) -> FXQuote:
        """
        Fetch a single FX quote.
        """
        raise NotImplementedError

    # --------------------------------------------------
    # Universes / discovery
    # --------------------------------------------------

    @abstractmethod
    def get_actively_traded_equities(self) -> list[dict]:
        """
        Return the actively traded equity universe.

        Each item must include:
        - symbol (str)
        - name (str | None)

        Used for discovery / seeding only.
        """
        raise NotImplementedError
    
    # --------------------------------------------------
    # Reference metadata (market-level)
    # --------------------------------------------------

    @abstractmethod
    def get_available_sectors(self) -> list[str]:
        """
        Return all known equity sectors.
        """
        raise NotImplementedError


    @abstractmethod
    def get_available_industries(self) -> list[str]:
        """
        Return all known equity industries.
        """
        raise NotImplementedError


    @abstractmethod
    def get_available_exchanges(self) -> list[dict]:
        """
        Return all known exchanges.

        Each item should include:
        - exchange (code)
        - name
        - countryCode (optional)
        - symbolSuffix (optional)
        - delay (optional)
        """
        raise NotImplementedError

    @abstractmethod
    def get_available_countries(self) -> list[str]:
        """
        Return ISO-3166 alpha-2 country codes supported by the provider.
        """
        raise NotImplementedError

    # --------------------------------------------------
    # Crypto
    # --------------------------------------------------

    @abstractmethod
    def get_cryptocurrencies(self) -> list[dict]:
        """
        Return available crypto instruments for discovery/seeding.
        """
        raise NotImplementedError

    @abstractmethod
    def get_crypto_quote(self, pair_symbol: str) -> dict:
        """
        Return a quote payload for a single crypto pair.
        """
        raise NotImplementedError

    @abstractmethod
    def get_crypto_quotes_bulk(self) -> list[dict]:
        """
        Return bulk crypto quotes where supported.
        """
        raise NotImplementedError

    # --------------------------------------------------
    # Commodities
    # --------------------------------------------------

    @abstractmethod
    def get_commodities(self) -> list[dict]:
        """
        Return available commodity instruments for discovery/seeding.
        """
        raise NotImplementedError

    @abstractmethod
    def get_commodity_quote(self, symbol: str) -> QuoteSnapshot:
        """
        Return a quote for a single commodity symbol.
        """
        raise NotImplementedError
