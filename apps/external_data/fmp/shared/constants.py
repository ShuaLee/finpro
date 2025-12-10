from django.conf import settings

FMP_API_KEY = settings.FMP_API_KEY

FMP_BASE = "https://financialmodelingprep.com/stable"

FMP_STOCK_PROFILE = f"{FMP_BASE}/profile"
FMP_STOCK_QUOTE = f"{FMP_BASE}/quote"
FMP_BULK_PROFILE = f"{FMP_BASE}/profile-bulk"
FMP_STOCK_LIST = f"{FMP_BASE}/stock-list"
