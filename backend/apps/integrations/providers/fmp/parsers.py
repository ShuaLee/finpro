from decimal import Decimal, InvalidOperation

from apps.integrations.exceptions import InvalidProviderResponse
from apps.integrations.shared.types import CompanyProfile, QuoteSnapshot


def _decimal(value):
    try:
        return Decimal(str(value)) if value is not None else None
    except (InvalidOperation, TypeError, ValueError):
        return None


def parse_quote_payload(raw: dict, *, source: str) -> QuoteSnapshot:
    symbol = (raw.get("symbol") or "").strip().upper()
    if not symbol:
        raise InvalidProviderResponse("Quote payload missing symbol.")

    volume = raw.get("volume")
    if volume is not None:
        try:
            volume = int(volume)
        except (TypeError, ValueError):
            volume = None

    return QuoteSnapshot(
        symbol=symbol,
        price=_decimal(raw.get("price")),
        change=_decimal(raw.get("change")),
        volume=volume,
        source=source,
    )


def parse_company_profile_payload(raw: dict) -> CompanyProfile:
    symbol = (raw.get("symbol") or "").strip().upper()
    if not symbol:
        raise InvalidProviderResponse("Profile payload missing symbol.")

    return CompanyProfile(
        symbol=symbol,
        name=raw.get("companyName") or raw.get("name"),
        currency=raw.get("currency"),
        exchange=raw.get("exchange") or raw.get("exchangeShortName"),
        sector=raw.get("sector"),
        industry=raw.get("industry"),
        country=raw.get("country"),
        website=raw.get("website"),
        description=raw.get("description"),
        image_url=raw.get("image"),
    )


def parse_profile_identity_payload(raw: dict) -> dict:
    profile = parse_company_profile_payload(raw)
    return {
        "company": {
            "symbol": profile.symbol,
            "name": profile.name or profile.symbol,
            "currency": profile.currency or "",
            "exchange": profile.exchange or "",
            "country": profile.country or "",
            "sector": profile.sector or "",
            "industry": profile.industry or "",
        },
        "identifiers": {
            "isin": (raw.get("isin") or "").strip().upper(),
            "cusip": (raw.get("cusip") or "").strip().upper(),
            "cik": (raw.get("cik") or "").strip(),
        },
    }


def parse_stock_list_row(raw: dict) -> dict:
    symbol = (raw.get("symbol") or "").strip().upper()
    if not symbol:
        raise InvalidProviderResponse("Stock list row missing symbol.")

    return {
        "symbol": symbol,
        "name": (raw.get("name") or raw.get("companyName") or symbol).strip(),
        "exchange": (raw.get("exchange") or raw.get("exchangeShortName") or "").strip(),
        "currency": (raw.get("currency") or "").strip(),
    }


def parse_actively_traded_row(raw: dict) -> str:
    symbol = (raw.get("symbol") or "").strip().upper()
    if not symbol:
        raise InvalidProviderResponse("Actively traded row missing symbol.")
    return symbol


def parse_active_equity_row(raw: dict) -> dict:
    symbol = (raw.get("symbol") or "").strip().upper()
    name = (raw.get("name") or symbol).strip()
    if not symbol:
        raise InvalidProviderResponse("Actively traded row missing symbol.")
    return {
        "symbol": symbol,
        "name": name,
    }


def parse_identifier_search_row(raw: dict) -> dict:
    symbol = (raw.get("symbol") or "").strip().upper()
    if not symbol:
        raise InvalidProviderResponse("Identifier search row missing symbol.")
    return {
        "symbol": symbol,
        "name": (raw.get("companyName") or raw.get("name") or symbol).strip(),
        "exchange": (raw.get("exchange") or raw.get("exchangeShortName") or "").strip(),
        "currency": (raw.get("currency") or "").strip(),
        "isin": (raw.get("isin") or "").strip().upper(),
        "cusip": (raw.get("cusip") or "").strip().upper(),
        "cik": (raw.get("cik") or "").strip(),
    }
