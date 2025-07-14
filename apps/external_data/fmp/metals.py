from django.conf import settings
from decimal import Decimal
import requests
import logging

logger = logging.getLogger(__name__)


def fetch_precious_metal_data(symbol: str):
    api_key = settings.FMP_API_KEY
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={api_key}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if not data:
            return None
        
        return {
            'price': Decimal(str(data[0].get("price", '0'))),
            'currency': data[0].get("currency"),
            'name': symbol.title()
        }
    
    except Exception as e:
        logger.warning(f"Failed to fetch metal {symbol}: {e}")
        return None
    
def apply_fmp_precious_metal_data(metal_obj, data: dict) -> bool:
    try:
        metal_obj.price = data.get("price", Decimal("0"))
        metal_obj.currency = data.get("currency")
        metal_obj.name = data.get("name", metal_obj.symbol)
        return True
    except Exception as e:
        logger.warning(f"Failed to apply FMP data to {metal_obj.symbol}: {e}")
        return False
