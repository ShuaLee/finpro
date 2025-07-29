from django.conf import settings
from assets.models.assets.stocks import Stock
from external_data.constants import FMP_FIELD_MAPPINGS
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import logging
import requests

logger = logging.getLogger(__name__)


def fetch_stock_data(ticker: str):
    """
    Fetch quote and profile data from FMP for a given ticker.
    """
    api_key = settings.FMP_API_KEY
    quote_url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={api_key}"
    profile_url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={api_key}"

    try:
        quote_response = requests.get(quote_url, timeout=5)
        quote_response.raise_for_status()
        quote_data = quote_response.json()
        quote = quote_data[0] if quote_data else None

        profile = {}
        try:
            profile_response = requests.get(profile_url, timeout=5)
            profile_response.raise_for_status()
            profile_data = profile_response.json()
            profile = profile_data[0] if profile_data else {}
        except Exception as e:
            logger.warning(f"Profile fetch failed for {ticker}: {e}")

        if not quote:
            logger.warning(f"no quote data returned for {ticker}")
            return None

        return {
            'quote': quote,
            'profile': profile
        }
    except Exception as e:
        logger.error(f"FMP fetch error for {ticker}: {e}")
        return None


def apply_fmp_stock_data(stock: Stock, quote: dict, profile: dict) -> bool:
    """
    Applies data from FMP `quote` and `profile` using static FMP_FIELD_MAPPINGS.
    """

    for model_field, api_field, source, data_type, required, default in FMP_FIELD_MAPPINGS:
        value = None
        if api_field:
            if source == 'quote':
                value = quote.get(api_field)
            elif source == 'profile':
                value = profile.get(api_field)

        if value is None and required:
            return False

        try:
            if data_type == 'decimal' and value is not None:
                value = Decimal(str(value)).quantize(
                    Decimal('0.0001'), rounding=ROUND_HALF_UP)
            elif data_type == 'integer' and value is not None:
                value = int(value)
            elif data_type == 'boolean' and value is not None:
                value = bool(value)
            elif data_type == 'string' and value is not None:
                value = str(value)
        except (InvalidOperation, ValueError, TypeError):
            value = default

        setattr(stock, model_field, value if value is not None else default)

    # Derived field: dividend_yield = lastDiv * 4 / price
    try:
        last_div = profile.get('lastDiv')
        if last_div and stock.price:
            dividend = Decimal(str(last_div)) * 4 / stock.price
            stock.dividend_yield = dividend.quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP)
    except Exception as e:
        logger.warning(f"Failed to calculate dividend_yield: {e}")
        stock.dividend_yield = None

    return True
