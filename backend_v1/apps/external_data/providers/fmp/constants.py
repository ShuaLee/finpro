from django.conf import settings


PROVIDER_NAME = "FMP"
FMP_BASE_URL = "https://financialmodelingprep.com/stable"
FMP_API_KEY = settings.FMP_API_KEY

# Transport defaults
FMP_TIMEOUT_SECONDS = getattr(settings, "EXTERNAL_DATA_TIMEOUT_SECONDS", 10)
FMP_MAX_RETRIES = getattr(settings, "EXTERNAL_DATA_MAX_RETRIES", 2)
FMP_RETRY_BACKOFF_SECONDS = getattr(settings, "EXTERNAL_DATA_RETRY_BACKOFF_SECONDS", 0.5)

# Shared quote endpoint
QUOTE_SHORT = "/quote-short"

# Equities
PROFILE = "/profile"
DIVIDENDS = "/dividends"
ACTIVELY_TRADING_LIST = "/actively-trading-list"
AVAILABLE_EXCHANGES = "/available-exchanges"
AVAILABLE_SECTORS = "/available-sectors"
AVAILABLE_INDUSTRIES = "/available-industries"

# FX
FOREX_LIST = "/forex-list"
FOREX_BATCH_QUOTES = "/batch-forex-quotes"
AVAILABLE_COUNTRIES = "/available-countries"

# Crypto
CRYPTO_LIST = "/cryptocurrency-list"
CRYPTO_BATCH_QUOTES = "/batch-crypto-quotes"

# Commodities
COMMODITIES_LIST = "/commodities-list"
COMMODITIES_QUOTE_SHORT = "/quote-short"
