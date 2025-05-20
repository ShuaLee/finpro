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

STOCK_FIELDS = [
    # (field_name, display_name, source, source_field)
    # Holding fields
    ('quantity', 'Quantity (Number)', 'holding', 'quantity'),
    ('purchase_price', 'Purchase Price (Number)', 'holding', 'purchase_price'),
    ('purchase_date', 'Purchase Date (Date)', 'holding', 'purchase_date'),
    # Asset fields
    ('ticker', 'Ticker (Text)', 'asset', 'ticker'),
    ('name', 'Company Name (Text)', 'asset', 'name'),
    ('price', 'Price (Number)', 'asset', 'price'),
    ('currency', 'Currency (Text)', 'asset', 'currency'),
    ('sector', 'Sector (Text)', 'asset', 'sector'),
    ('industry', 'Industry (Text)', 'asset', 'industry'),
    ('dividend_yield', 'Dividend Yield (Number)', 'asset', 'dividend_yield'),
    ('pe_ratio', 'P/E Ratio (Number)', 'asset', 'pe_ratio'),
    ('quote_type', 'Quote Type (Text)', 'asset', 'quote_type'),
    ('average_volume', 'Average Volume (Number)', 'asset', 'average_volume'),
    ('volume', 'Volume (Number)', 'asset', 'volume'),
    # Calculated fields
    ('total_value', 'Total Value (Number)', 'calculated', 'total_value'),
    ('total_investment', 'Total Investment (Number)',
     'calculated', 'total_investment'),
    ('performance', 'Performance (%) (Number)', 'calculated', 'performance'),
]

CALCULATION_FORMULAS = {
    'total_value': 'quantity * price',
    'total_investment': 'quantity * purchase_price',
    'performance': '((quantity * price) - (quantity * purchase_price)) / (quantity * purchase_price) * 100',
}

FIELD_DATA_TYPES = {
    'ticker': 'string',
    'name': 'string',
    'price': 'decimal',
    'quantity': 'decimal',
    'purchase_price': 'decimal',
    'purchase_date': 'date',
    'currency': 'string',
    'sector': 'string',
    'industry': 'string',
    'dividend_yield': 'decimal',
    'pe_ratio': 'decimal',
    'quote_type': 'string',
    'average_volume': 'decimal',
    'volume': 'decimal',
    'total_value': 'decimal',
    'total_investment': 'decimal',
    'performance': 'decimal',
}
