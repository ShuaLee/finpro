import os


PLAID_ENV = os.getenv("PLAID_ENV", "sandbox").strip().lower()
PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID", "")
PLAID_SECRET = os.getenv("PLAID_SECRET", "")

PLAID_TIMEOUT_SECONDS = int(os.getenv("PLAID_TIMEOUT_SECONDS", "15"))
PLAID_MAX_RETRIES = int(os.getenv("PLAID_MAX_RETRIES", "2"))
PLAID_RETRY_BACKOFF_SECONDS = float(os.getenv("PLAID_RETRY_BACKOFF_SECONDS", "0.5"))

PLAID_BASE_URL_BY_ENV = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com",
}


def plaid_base_url() -> str:
    return PLAID_BASE_URL_BY_ENV.get(PLAID_ENV, PLAID_BASE_URL_BY_ENV["sandbox"])

