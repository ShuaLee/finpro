from accounts.models.account import AccountType
from accounts.models.details import (
    StockSelfManagedDetails,
    StockManagedDetails,
    CustomAccountDetails,
)

ACCOUNT_TYPE_DETAILS_MAP = {
    AccountType.STOCK_SELF_MANAGED: StockSelfManagedDetails,
    AccountType.STOCK_MANAGED: StockManagedDetails,
    AccountType.CUSTOM: CustomAccountDetails,
    # Crypto + Metal don’t need detail models
}