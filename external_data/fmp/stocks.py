from django.conf import settings
from assets.constants import ASSET_SCHEMA_CONFIG
from assets.models import Stock
from decimal import Decimal, InvalidOperation
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
    Applies data from FMP `quote` and `profile` into a Stock instance
    using the unified asset schema config.
    """
    config = ASSET_SCHEMA_CONFIG.get('stock', {}).get('asset', {})

    if not config:
        logger.warning("No stock asset config found in ASSET_SCHEMA_CONFIG.")
        return False

    for field_name, field_cfg in config.items():
        # default to quote if not specified
        source = field_cfg.get('source', 'quote')
        api_field = field_cfg.get('api_field', field_name)
        data_type = field_cfg.get('data_type')
        decimal_places = field_cfg.get('decimal_spaces', None)

        value = None
        if source == 'quote':
            value = quote.get(api_field)
        elif source == 'profile':
            value = profile.get(api_field)

        # Convert value based on data type
        if value is not None:
            try:
                if data_type == 'decimal':
                    value = Decimal(str(value))
                    if decimal_places is not None:
                        value = round(value, decimal_places)
                elif data_type == 'integer':
                    value = int(value)
                elif data_type == 'string':
                    value = str(value)
            except (InvalidOperation, ValueError, TypeError) as e:
                logger.warning(f"Failed to parse {field_name}: {e}")
                value = None

        setattr(stock, field_name, value)

    # Handle derived field (will delete later once FMP membership changes)
    try:
        last_div = profile.get('lastDiv')
        if last_div and stock.price:
            stock.dividend_yield = Decimal(str(last_div)) * 4 / stock.price
    except Exception as e:
        logger.warning(f"Failed to calculate dividend_yield: {e}")
        stock.dividend_yield = None

    return True
