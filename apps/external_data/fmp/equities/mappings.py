EQUITY_PROFILE_MAP = {
    "exchangeShortName": "exchange",
    "exchange": "exchange_full_name",
    "currency": "asset__currency",
    "country": "country",
    "ipoDate": "ipo_date",
    "sector": "sector",
    "industry": "industry",
    "isEtf": "is_etf",
    "isAdr": "is_adr",
    "isFund": "is_mutual_fund",
    "companyName": "asset__name",
    "isin": "isin",
    "cusip": "cusip",
    "cik": "cik",
}

EQUITY_QUOTE_MAP = {
    # --- Core Quote Fields ---
    "price": "last_price",
    "change": "change",
    "changesPercentage": "change_percent",
    "previousClose": "previous_close",
    "open": "open_price",
    "dayHigh": "high_price",
    "dayLow": "low_price",
    "volume": "volume",
    "avgVolume": "avg_volume",
    "marketCap": "market_cap",

    # --- Extended Metrics ---
    "yearHigh": "year_high",
    "yearLow": "year_low",
    "eps": "eps",
    "pe": "pe_ratio",
    "lastDiv": "dividend_per_share",
    "yield": "dividend_yield",
}
