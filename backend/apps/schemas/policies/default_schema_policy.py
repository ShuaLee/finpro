class DefaultSchemaPolicy:
    DEFAULT_COLUMNS_BY_ASSET_TYPE = {
        "equity": [
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
        "commodity": [
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
        "precious_metal": [
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
        "real_estate": [
            "quantity",
            "average_purchase_price",
            "current_value",
            "cost_basis",
            "unrealized_gain",
            "unrealized_gain_pct",
        ],
    }

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
    def default_identifiers_for_asset_type(cls, asset_type):
        if not asset_type:
            return []
        return cls.DEFAULT_COLUMNS_BY_ASSET_TYPE.get(asset_type.slug, [])

    @classmethod
    def default_identifiers_for_account_type(cls, account_type):
        if getattr(account_type, "allowed_asset_types", None):
            asset_types = list(account_type.allowed_asset_types.all()[:2])
            if len(asset_types) == 1:
                identifiers = cls.default_identifiers_for_asset_type(asset_types[0])
                if identifiers:
                    return identifiers
        return cls.DEFAULT_COLUMNS.get(account_type.slug, [])
