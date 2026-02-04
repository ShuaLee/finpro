class DefaultSchemaPolicy:
    DEFAULT_COLUMNS = {
        "brokerage": [
            "quantity",
            "price",
            "asset_currency",
            "market_value",
            "current_value",
            "dividend_yield",
            "trailing_12m_dividend",
        ],
        "crypto-wallet": [
            "quantity",
            "price",
            "asset_currency",
            "market_value",
            "current_value",
        ],
    }

    @classmethod
    def default_identifiers_for_account_type(cls, account_type):
        return cls.DEFAULT_COLUMNS.get(account_type.slug, [])
