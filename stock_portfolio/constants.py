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

CURRENCY_CHOICES = [
    (currency.alpha_3, currency.name)
    for currency in pycountry.currencies
]

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
