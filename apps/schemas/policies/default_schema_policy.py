class DefaultSchemaPolicy:
    DEFAULT_COLUMNS = {
        "brokerage": [
            "quantity",
            "price",
            "asset_currency",
            "market_value",
            "current_value",
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
