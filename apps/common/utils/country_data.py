"""
common.utils.country_data
~~~~~~~~~~~~~~~~~~~~~~~~~~
Provides cached country and currency constants with validation support.
"""

import pycountry
from django.core.exceptions import ValidationError
from functools import lru_cache

# ✅ Cached choices with deduplication


@lru_cache(maxsize=1)
def get_country_choices():
    seen = set()
    choices = []
    for country in pycountry.countries:
        if country.alpha_2 not in seen:
            seen.add(country.alpha_2)
            choices.append((country.alpha_2, country.name))
    return sorted(choices, key=lambda x: x[1])  # Alphabetical by name


@lru_cache(maxsize=1)
def get_currency_choices():
    seen = set()
    choices = []
    for cur in pycountry.currencies:
        if cur.alpha_3 not in seen:
            seen.add(cur.alpha_3)
            choices.append((cur.alpha_3, cur.name))
    return sorted(choices, key=lambda x: x[1])

# ✅ Extract valid codes


@lru_cache(maxsize=1)
def valid_country_codes():
    return {c.alpha_2 for c in pycountry.countries}


@lru_cache(maxsize=1)
def valid_currency_codes():
    return {cur.alpha_3 for cur in pycountry.currencies}

# ✅ Validators


def validate_country_code(code: str):
    code = (code or "").upper()
    if code not in valid_country_codes():
        raise ValidationError(
            f"Invalid country code '{code}'. Must be ISO 3166-1 alpha-2 (e.g., US, GB, CA)."
        )


def validate_currency_code(code: str):
    code = (code or "").upper()
    if code not in valid_currency_codes():
        raise ValidationError(
            f"Invalid currency code '{code}'. Must be ISO 4217 (e.g., USD, EUR, JPY)."
        )
