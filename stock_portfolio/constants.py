SCHEMA_COLUMN_CONFIG = {
    'asset': {
        'ticker': {
            'data_type': 'string',
            'editable': False,
            'field_path': 'holding.stock.ticker',
        },
        'price': {
            'data_type': 'decimal',
            'editable': True,
            'field_path': 'holding.stock.price',
        },
        'name': {
            'data_type': 'string',
            'editable': True,
            'field_path': 'holding.stock.name',
        },
    },
    'holding': {
        'quantity': {
            'data_type': 'decimal',
            'editable': True,
            'field_path': 'holding.quantity',
        },
        'purchase_price': {
            'data_type': 'decimal',
            'editable': True,
            'field_path': 'holding.purchase_price',
        },
        'holding.ticker': {
            'data_type': 'string',
            'editable': True,
            'field_path': 'holding.stock.ticker',
        },
    },
    'custom': {
        None: {
            'data_type': 'string',  # flexible
            'editable': True,
            'field_path': None,
        }
    },
    'calculated': {
        'current_value': {
            'data_type': 'decimal',
            'editable': False,
            'formula_required': True,
        }
    }
}

DEFAULT_STOCK_SCHEMA_COLUMNS = [
    {
        'title': 'Ticker',
        'data_type': 'string',
        'source': 'asset',
        'source_field': 'ticker',
        'editable': False,
        'is_deletable': False,
    },
    {
        'title': 'Quantity',
        'data_type': 'decimal',
        'source': 'holding',
        'source_field': 'quantity',
        'editable': True,
        'is_deletable': False,
    },
    {
        'title': 'Price',
        'data_type': 'decimal',
        'source': 'asset',
        'source_field': 'price',
        'editable': True,
        'is_deletable': False,
    },
    {
        'title': 'Value',
        'data_type': 'decimal',
        'source': 'calculated',
        'source_field': 'current_value',
        'editable': False,
        'is_deletable': False,
        'formula': 'quantity * price',
    },
]

# Optional: for runtime validation
EDITABLE_FIELD_RULES = {
    ('holding', 'quantity'): float,
    ('holding', 'purchase_price'): float,
    ('holding', 'holding.ticker'): str,
    ('asset', 'price'): float,
    ('asset', 'industry'): str,
    ('asset', 'sector'): str,
    # Add more as needed
}

EDITABLE_COLUMN_HANDLERS = {
    ('holding', 'quantity'): {
        'field_path': 'holding.quantity',
        'type': float,
        'error': "Quantity must be a number."
    },
    ('holding', 'purchase_price'): {
        'field_path': 'holding.purchase_price',
        'type': float,
        'error': "Purchase price must be a number."
    },
    ('holding', 'holding.ticker'): {
        'field_path': 'holding.stock.ticker',
        'type': str,
        'error': "Ticker must be a string."
    },
    ('asset', 'price'): {
        'field_path': 'holding.stock.price',
        'type': float,
        'error': "Price must be a number."
    },
    # Add more as needed
}




# ------------------------------------------------- #

PREDEFINED_COLUMNS = {
    'stock': [
        {'field': 'ticker', 'label': 'Stock Ticker',
            'type': 'string', 'editable': False},
        {'field': 'last_price', 'label': 'Stock Price', 'type': 'decimal'},
    ],
    'holding': [
        {'field': 'purchase_price', 'label': 'Purchase Price', 'type': 'decimal'},
        {'field': 'shares', 'label': 'Shares Owned', 'type': 'decimal'},
    ],
}

PREDEFINED_CALCULATED_COLUMNS = {
    'Total Investment': {
        'formula': 'shares * last_price',
        'dependencies': [
            {'source': 'holding', 'field': 'shares'},
            {'source': 'stock', 'field': 'last_price'},
        ],
        'type': 'decimal',
    },
}

SKELETON_SCHEMA = {
    'name': 'Default Schema',
    'columns': {
        'stock': [
            {'field': 'ticker', 'label': 'Stock Ticker',
                'type': 'string', 'editable': False},
            {'field': 'last_price', 'label': 'Stock Price', 'type': 'decimal'},
        ],
        'holding': [
            {'field': 'shares', 'label': 'Shares Owned', 'type': 'decimal'},
        ],
    }
}

CALCULATION_FORMULAS = {
    'total_value': 'quantity * price',
    'total_investment': 'quantity * purchase_price',
    'performance': '((quantity * price) - (quantity * purchase_price)) / (quantity * purchase_price) * 100',
}
