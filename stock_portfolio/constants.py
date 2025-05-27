import pycountry

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
