from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional

# --------------------------------------------------
# Identifier bundle
# --------------------------------------------------


@dataclass(frozen=True)
class EquityIdentifierBundle:
    """
    Canonical identifier set for an asset as returned by a provider.

    Values may be None if not supplied by the provider.
    """
    ticker: Optional[str] = None
    isin: Optional[str] = None
    cusip: Optional[str] = None
    cik: Optional[str] = None

# --------------------------------------------------
# Equity identity result
# --------------------------------------------------


@dataclass(frozen=True)
class EquityIdentity:
    """
    Represents a resolved equity identity from a provider.

    This proves the symbol exists (or existed) and ties together
    profile metadata and identifiers.
    """
    symbol: str
    profile: Dict[str, Any]
    identifiers: EquityIdentifierBundle

# --------------------------------------------------
# Quote snapshot
# --------------------------------------------------


@dataclass(frozen=True)
class QuoteSnapshot:
    """
    Lightweight, fast-moving price snapshot.
    """
    price: Optional[Decimal]
    change: Optional[Decimal] = None
    volume: Optional[int] = None


# --------------------------------------------------
# FX quote
# --------------------------------------------------

@dataclass(frozen=True)
class FXQuote:
    """
    Represents a foreign exchange rate.
    """
    base: str
    quote: str
    rate: Decimal
