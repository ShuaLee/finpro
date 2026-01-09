SYSTEM_ASSET_TYPES = [
    {
        "slug": "equity",
        "name": "Equity",
        "identifier_rules": ["TICKER", "ISIN", "CUSIP", "CIK"],
    },
    {
        "slug": "crypto",
        "name": "Crypto",
        "identifier_rules": ["BASE_SYMBOL", "PAIR_SYMBOL"],
    },
    {
        "slug": "bond",
        "name": "Bond",
        "identifier_rules": ["ISIN", "CUSIP"],
    },
    {
        "slug": "metal",
        "name": "Metal",
        "identifier_rules": ["TICKER"],
    },
    {
        "slug": "real_estate",
        "name": "Real Estate",
        "identifier_rules": [],
    },
    {
        "slug": "custom",
        "name": "Custom",
        "identifier_rules": [],
    },
]

