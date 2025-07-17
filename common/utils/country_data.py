"""
common.utils.country_data
~~~~~~~~~~~~~~~~~~~
Provides cached country and currency constants with validation support.
"""

import pycountry
from django.core.exceptions import ValidationError
from functools import lru_cache


# ✅ Cached choices so they are computed only once per process
@lru_cache(maxsize=1)
def get_country_choices():
    return [(c.alpha_2, c.name) for c in pycountry.countries]


@lru_cache(maxsize=1)
def get_currency_choices():
    return [(cur.alpha_3, cur.name) for cur in pycountry.currencies]


# ✅ Extract valid codes for quick lookups
@lru_cache(maxsize=1)
def valid_country_codes():
    return {c.alpha_2 for c in pycountry.countries}


@lru_cache(maxsize=1)
def valid_currency_codes():
    return {cur.alpha_3 for cur in pycountry.currencies}


# ✅ Validators for strict enforcement
def validate_country_code(code: str):
    if code not in valid_country_codes():
        raise ValidationError(f"Invalid country code: '{code}'.")


def validate_currency_code(code: str):
    if code not in valid_currency_codes():
        raise ValidationError(f"Invalid currency code: '{code}'.")
