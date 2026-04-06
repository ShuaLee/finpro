from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class QuoteSnapshot:
    symbol: str
    price: Decimal | None
    change: Decimal | None = None
    volume: int | None = None
    source: str = ""


@dataclass(frozen=True)
class CompanyProfile:
    symbol: str
    name: str | None = None
    currency: str | None = None
    exchange: str | None = None
    sector: str | None = None
    industry: str | None = None
    country: str | None = None
    website: str | None = None
    description: str | None = None
    image_url: str | None = None
