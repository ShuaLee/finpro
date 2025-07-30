from common.models import FXRate
from decimal import Decimal

class FXEngine:
    def __init__(self, base_currency="USD"):
        self.base = base_currency.upper()
        self.rates = self._get_rates()

    def _get_rates(self):
        rates = FXRate.objects.filter(from_currency=self.base)
        return {r.to_currency.upper(): r.rate for r in rates}
    
    def convert(self, amount: Decimal, to_currency: str):
        to_currency = to_currency.upper()
        if to_currency == self.base:
            return amount
        
        rate = self.rates.get(to_currency)
        if not rate:
            raise Exception(f"No FX rate found for {self.base} -> {to_currency}")