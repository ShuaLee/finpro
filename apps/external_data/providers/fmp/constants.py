from django.conf import settings


# --------------------------------------------------
# Provider identity
# --------------------------------------------------

PROVIDER_NAME = "FMP"


# --------------------------------------------------
# Base configuration
# --------------------------------------------------

FMP_BASE_URL = "https://financialmodelingprep.com/stable"

FMP_API_KEY = settings.FMP_API_KEY


# --------------------------------------------------
# Common query parameters
# --------------------------------------------------

DEFAULT_LIMIT = 1000
DEFAULT_PAGE = 0


# ==================================================
# Identity & Identifier Resolution
# ==================================================

SEARCH_CIK = "/search-cik"
SEARCH_CUSIP = "/search-cusip"
SEARCH_ISIN = "/search-isin"

PROFILE = "/profile"
PROFILE_BY_CIK = "/profile-cik"


# ==================================================
# Symbol Discovery & Resolution
# ==================================================

SEARCH_SYMBOL = "/search-symbol"
SEARCH_NAME = "/search-name"
SYMBOL_CHANGES = "/symbol-change"
EXCHANGE_VARIANTS = "/search-exchange-variants"


# ==================================================
# Equity Quotes
# ==================================================

QUOTE = "/quote"
QUOTE_SHORT = "/quote-short"

BATCH_QUOTE = "/batch-quote"
BATCH_QUOTE_SHORT = "/batch-quote-short"


# ==================================================
# Dividends & Corporate Actions
# ==================================================

DIVIDENDS = "/dividends"
HISTORICAL_DIVIDENDS = "/historical-dividends"


# ==================================================
# Universes / Listings
# ==================================================

STOCK_LIST = "/stock-list"
FINANCIAL_STATEMENT_SYMBOL_LIST = "/financial-statement-symbol-list"
ACTIVELY_TRADING_LIST = "/actively-trading-list"
DELISTED_COMPANIES = "/delisted-companies"


# ==================================================
# Reference Metadata
# ==================================================

AVAILABLE_EXCHANGES = "/available-exchanges"
AVAILABLE_SECTORS = "/available-sectors"
AVAILABLE_INDUSTRIES = "/available-industries"
AVAILABLE_COUNTRIES = "/available-countries"


# ==================================================
# Forex
# ==================================================

FOREX_LIST = "/forex-list"
FOREX_BATCH_QUOTES = "/batch-forex-quotes"


# ==================================================
# Cryptocurrencies
# ==================================================

CRYPTO_LIST = "/cryptocurrency-list"
CRYPTO_BATCH_QUOTES = "/batch-crypto-quotes"


# ==================================================
# Commodities
# ==================================================

COMMODITIES_LIST = "/commodities-list"
COMMODITIES_BATCH_QUOTES = "/batch-commodity-quotes"
