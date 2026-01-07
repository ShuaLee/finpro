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
