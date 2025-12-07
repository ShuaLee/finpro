SYSTEM_CONSTRAINT_DEFINITIONS = [
    # Decimal
    {
        "data_type": "decimal",
        "constraint_type": "decimal_places",
        "default": "2",
    },
    {
        "data_type": "decimal",
        "constraint_type": "min_value",
        "default": "0",
    },
    {
        "data_type": "decimal",
        "constraint_type": "max_value",
        "default": None,    # unlimited
    },

    # String
    {
        "data_type": "string",
        "constraint_type": "max_length",
        "default": "255",
    },

    # URL
    {
        "data_type": "url",
        "constraint_type": "max_length",
        "default": "2048",
    },

    # Regex defaults (none)
]
