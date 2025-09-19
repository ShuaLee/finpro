import pycountry

COUNTRY_CHOICES = [(c.alpha_2, c.name) for c in pycountry.countries]
VALID_COUNTRY_CODES = {c.alpha_2 for c in pycountry.countries}

def validate_country_code(value: str):
    """
    Ensure value is a valid ISO-3166 alpha-2 country code.
    """
    if value not in VALID_COUNTRY_CODES:
        raise ValueError(f"Invalid country code: {value}")
    return value