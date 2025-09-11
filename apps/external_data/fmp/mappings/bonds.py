from external_data.fmp.normalize import _to_decimal, _to_int, _to_str, _to_date

BOND_PROFILE_MAP = {
    "issuer": ("issuer", _to_str),
    "cusip": ("cusip", _to_str),
    "isin": ("isin", _to_str),
    "bond_type": ("bondType", _to_str),
    "country": ("country", _to_str),
    "coupon_rate": ("coupon", _to_decimal),
    "coupon_frequency": ("couponFrequency", _to_str),
    "issue_date": ("issueDate", _to_date),
    "maturity_date": ("maturityDate", _to_date),
    "call_date": ("callDate", _to_date),
    "par_value": ("parValue", _to_decimal),
    "issue_size": ("issueSize", _to_int),
    "outstanding_amount": ("outstandingAmount", _to_int),
    "rating": ("rating", _to_str),
}

BOND_QUOTE_MAP = {
    "last_price": ("price", _to_decimal),
    "yield_to_maturity": ("yieldToMaturity", _to_decimal),
    "yield_to_call": ("yieldToCall", _to_decimal),
    "current_yield": ("yield", _to_decimal),
    "accrued_interest": ("accruedInterest", _to_decimal),
    "currency": ("currency", _to_str),
    "volume": ("volume", _to_int),
}
