import pycountry

CURRENCY_CHOICES = [
    (currency.alpha_3, currency.name)
    for currency in pycountry.currencies
]