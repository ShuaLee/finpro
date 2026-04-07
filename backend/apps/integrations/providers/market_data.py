from abc import ABC, abstractmethod

from apps.integrations.shared.types import CompanyProfile, QuoteSnapshot


class MarketDataProvider(ABC):
    name: str

    @abstractmethod
    def get_quote(self, symbol: str) -> QuoteSnapshot:
        raise NotImplementedError

    @abstractmethod
    def get_company_profile(self, symbol: str) -> CompanyProfile:
        raise NotImplementedError

    @abstractmethod
    def get_stock_list(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_actively_traded_symbols(self) -> set[str]:
        raise NotImplementedError

    @abstractmethod
    def get_actively_traded_rows(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_profile_with_identifiers(self, symbol: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def search_by_isin(self, isin: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def search_by_cusip(self, cusip: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def search_by_cik(self, cik: str) -> list[dict]:
        raise NotImplementedError
