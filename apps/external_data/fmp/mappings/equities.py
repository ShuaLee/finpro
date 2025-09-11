from external_data.fmp.normalize import _to_decimal, _to_int, _to_str, _to_date

EQUITY_PROFILE_MAP = {
    # Identification
    "exchange": ("exchangeShortName", _to_str),
    "exchange_full_name": ("exchange", _to_str),
    "currency": ("currency", _to_str),
    "country": ("country", _to_str),
    "cusip": ("cusip", _to_str),
    "isin": ("isin", _to_str),
    "ipo_date": ("ipoDate", _to_date),

    # Classification
    "sector": ("sector", _to_str),
    "industry": ("industry", _to_str),
    "is_etf": ("isEtf", bool),
    "is_adr": ("isAdr", bool),
    "is_mutual_fund": ("isFund", bool),

    # Dividend info
    "dividend_per_share": ("lastDiv", _to_decimal),
    "dividend_yield": ("dividendYield", _to_decimal),
    "dividend_frequency": ("dividendFrequency", _to_str),
    "ex_dividend_date": ("exDividendDate", _to_date),
    "dividend_payout_ratio": ("payoutRatio", _to_decimal),

    # Mutual fund specific
    "expense_ratio": ("expenseRatio", _to_decimal),
    "fund_family": ("fundFamily", _to_str),
    "fund_category": ("category", _to_str),
    "inception_date": ("inceptionDate", _to_date),
    "total_assets": ("totalAssets", _to_int),
    "turnover_ratio": ("turnoverRatio", _to_decimal),

    # ETF specific
    "underlying_index": ("etfIndex", _to_str),
    "aum": ("aum", _to_int),
    "holdings_count": ("holdingsCount", _to_int),
    "tracking_error": ("trackingError", _to_decimal),

    # Closed-End Fund
    "premium_discount": ("premiumDiscount", _to_decimal),

    # Preferred Shares
    "preferred_par_value": ("preferredParValue", _to_decimal),
    "preferred_coupon_rate": ("preferredCouponRate", _to_decimal),
    "call_date": ("callDate", _to_date),

    # ESG
    "esg_score": ("esgScore", _to_decimal),
    "carbon_intensity": ("carbonIntensity", _to_decimal),
}

EQUITY_QUOTE_MAP = {
    # Market data
    "last_price": ("price", _to_decimal),
    "open_price": ("open", _to_decimal),
    "high_price": ("dayHigh", _to_decimal),
    "low_price": ("dayLow", _to_decimal),
    "previous_close_price": ("previousClose", _to_decimal),
    "volume": ("volume", _to_int),
    "average_volume": ("avgVolume", _to_int),
    "market_cap": ("marketCap", _to_int),
    "shares_outstanding": ("sharesOutstanding", _to_int),
    "beta": ("beta", _to_decimal),

    # Valuation ratios
    "eps": ("eps", _to_decimal),
    "pe_ratio": ("pe", _to_decimal),
    "pb_ratio": ("priceToBook", _to_decimal),
    "ps_ratio": ("priceToSales", _to_decimal),
    "peg_ratio": ("pegRatio", _to_decimal),

    # Mutual fund specific
    "nav": ("nav", _to_decimal),
}
