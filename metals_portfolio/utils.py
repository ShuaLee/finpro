from django.conf import settings
import logging
import requests

logger = logging.getLogger(__name__)

api_key = settings.FMP_API_KEY


def get_precious_metal_price(symbol: str):
    try:
        url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={api_key}"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data[0]['price'] if data else None
    except Exception as e:
        logger.warning(f"API error for {symbol}: {str(e)}")
        return None
