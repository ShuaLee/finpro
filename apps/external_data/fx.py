from datetime import timedelta
from django.conf import settings
from django.utils.timezone import now
from common.models import FXRate
import requests


def get_fx_rate(from_currency, to_currency):
    if from_currency == to_currency:
        return 1.0

    # Try from DB
    try:
        fx = FXRate.objects.get(
            from_currency=from_currency, to_currency=to_currency)
        if now() - fx.updated_at < timedelta(hours=12):
            return float(fx.rate)
    except FXRate.DoesNotExist:
        fx = None

    # Fetch from API
    url = f"https://financialmodelingprep.com/api/v3/quote/{from_currency}{to_currency}"
    params = {'apikey': settings.FMP_API_KEY}
    response = requests.get(url, params=params)
    data = response.json()

    try:
        rate = float(data[0]['price'])  # FMP returns a list with one dict
        if fx:
            fx.rate = rate
            fx.updated_at = now()
            fx.save()
        else:
            FXRate.objects.create(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=rate
            )
        return rate
    except Exception as e:
        return None
