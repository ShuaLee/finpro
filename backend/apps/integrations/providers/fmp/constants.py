from django.conf import settings


PROVIDER_NAME = "FMP"
FMP_BASE_URL = getattr(settings, "FMP_BASE_URL", "https://financialmodelingprep.com/stable")
FMP_API_KEY = getattr(settings, "FMP_API_KEY", "")
FMP_TIMEOUT_SECONDS = getattr(settings, "INTEGRATIONS_TIMEOUT_SECONDS", 10)
FMP_MAX_RETRIES = getattr(settings, "INTEGRATIONS_MAX_RETRIES", 2)
FMP_RETRY_BACKOFF_SECONDS = getattr(settings, "INTEGRATIONS_RETRY_BACKOFF_SECONDS", 0.5)

# Stable endpoints we can rely on for the current build.
QUOTE_SHORT = "/quote-short"
PROFILE = "/profile"
DIVIDENDS = "/dividends"
STOCK_LIST = "/stock-list"
ACTIVELY_TRADING_LIST = "/actively-trading-list"
CRYPTOCURRENCY_LIST = "/cryptocurrency-list"
COMMODITIES_LIST = "/commodities-list"
FOREX_LIST = "/forex-list"
AVAILABLE_COUNTRIES = "/available-countries"
SEARCH_ISIN = "/search-isin"
SEARCH_CUSIP = "/search-cusip"
PROFILE_CIK = "/profile-cik"
