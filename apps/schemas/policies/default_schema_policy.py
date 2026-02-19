class DefaultSchemaPolicy:
    DEFAULT_COLUMNS = {
        "brokerage": [
            "quantity",
            "average_purchase_price",
            "price",
            "asset_currency",
            "market_value",
            "current_value",
            "cost_basis",
            "unrealized_gain",
            "unrealized_gain_pct",
            "dividend_yield",
            "trailing_12m_dividend",
        ],
        "crypto-wallet": [
            "quantity",
            "average_purchase_price",
            "price",
            "asset_currency",
            "market_value",
            "current_value",
            "cost_basis",
            "unrealized_gain",
            "unrealized_gain_pct",
        ],
        "crypto_wallet": [
            "quantity",
            "average_purchase_price",
            "price",
            "asset_currency",
            "market_value",
            "current_value",
            "cost_basis",
            "unrealized_gain",
            "unrealized_gain_pct",
        ],
        "crypto": [
            "quantity",
            "average_purchase_price",
            "price",
            "asset_currency",
            "market_value",
            "current_value",
            "cost_basis",
            "unrealized_gain",
            "unrealized_gain_pct",
        ],
    }

    @classmethod
    def default_identifiers_for_account_type(cls, account_type):
        return cls.DEFAULT_COLUMNS.get(account_type.slug, [])
