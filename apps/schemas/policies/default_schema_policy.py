class DefaultSchemaPolicy:
    DEFAULT_COLUMNS = {
        "brokerage": [
            "quantity",
            "price",
            "current_value",
        ],
        "crypto": [
            "quantity",
            "price",
            "current_value",
        ],
    }

    @classmethod
    def default_identifiers_for_account_type(cls, account_type):
        return cls.DEFAULT_COLUMNS.get(account_type.slug, [])
