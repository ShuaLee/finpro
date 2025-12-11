from django.conf import settings

FMP_API_KEY = settings.FMP_API_KEY

FMP_BASE = "https://financialmodelingprep.com/stable"

FMP_ACTIVELY_TRADING = f"{FMP_BASE}/actively-trading-list"
FMP_BULK_PROFILE = f"{FMP_BASE}/profile-bulk"
FMP_DIVIDENDS = f"{FMP_BASE}/dividends"
FMP_STOCK_LIST = f"{FMP_BASE}/stock-list"
FMP_STOCK_PROFILE = f"{FMP_BASE}/profile"
FMP_STOCK_QUOTE_SHORT = f"{FMP_BASE}/quote-short"
FMP_ISIN = f"{FMP_BASE}/search-isin"
FMP_CIK = f"{FMP_BASE}/profile-cik"
FMP_CUSIP = f"{FMP_BASE}/search-cusip"