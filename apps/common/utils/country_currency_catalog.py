# common/utils/country_currency_catalog.py

from functools import lru_cache
from django.core.exceptions import ValidationError

# ✅ Curated Common Countries
COMMON_COUNTRIES = {
    "US": "United States",
    "GB": "United Kingdom",
    "CA": "Canada",
    "JP": "Japan",
    "DE": "Germany",
    "FR": "France",
    "AU": "Australia",
    "IN": "India",
    "CN": "China",
    "CH": "Switzerland"
}

# ✅ Curated Common Currencies
COMMON_CURRENCIES = {
    "USD": "US Dollar",
    "EUR": "Euro",
    "GBP": "British Pound",
    "JPY": "Japanese Yen",
    "AUD": "Australian Dollar",
    "CAD": "Canadian Dollar",
    "CHF": "Swiss Franc",
    "CNY": "Chinese Yuan",
    "INR": "Indian Rupee"
}


# 🔽 Public API

@lru_cache(maxsize=1)
def get_common_country_choices():
    return sorted(COMMON_COUNTRIES.items(), key=lambda x: x[1])


@lru_cache(maxsize=1)
def get_common_currency_choices():
    return sorted(COMMON_CURRENCIES.items(), key=lambda x: x[1])


def validate_country_code(code: str):
    code = (code or "").upper()
    if code not in COMMON_COUNTRIES:
        raise ValidationError(f"Invalid country code '{code}'. Must be one of: {', '.join(COMMON_COUNTRIES.keys())}")
    return code


def validate_currency_code(code: str):
    code = (code or "").upper()
    if code not in COMMON_CURRENCIES:
        raise ValidationError(f"Invalid currency code '{code}'. Must be one of: {', '.join(COMMON_CURRENCIES.keys())}")
    return code
