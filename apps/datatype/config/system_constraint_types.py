SYSTEM_CONSTRAINT_TYPES = [
    {
        "slug": "decimal_places",
        "name": "Decimal Places",
        "description": "Number of digits allowed after the decimal point.",
        "value_data_type": "decimal",     # stored as text but semantically decimal
        "applies_to": ["decimal"],
    },
    {
        "slug": "min_value",
        "name": "Minimum Value",
        "description": "Lowest allowed numerical value.",
        "value_data_type": "decimal",
        "applies_to": ["decimal"],
    },
    {
        "slug": "max_value",
        "name": "Maximum Value",
        "description": "Highest allowed numerical value.",
        "value_data_type": "decimal",
        "applies_to": ["decimal"],
    },
    {
        "slug": "max_length",
        "name": "Maximum Length",
        "description": "Maximum number of characters allowed.",
        "value_data_type": "decimal",     # stored integer-like, but decimal works fine
        "applies_to": ["string", "url"],
    },
    {
        "slug": "regex",
        "name": "Regex Pattern",
        "description": "Regular expression that the value must match.",
        "value_data_type": "string",
        "applies_to": ["string", "url"],
    },
]
