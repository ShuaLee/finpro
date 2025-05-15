SOURCE_FIELD_CHOICES = {
    'asset': {
        'stockportfolio': [
            ('name', 'Name (Text)', 'Company Name'),
            ('price', 'Price (Number)', 'Share Price'),
            ('currency', 'Currency (Text)', 'Currency'),
            ('average_volume', 'Average Volume (Number)', 'Average Volumne'),
            ('volume', 'Volume (Number)', 'Volume'),
            ('dividend_yield', 'Dividend Yield (Number)', 'Dividend Yield'),
            ('pe_ratio', 'PE Ratio (Number)', 'PE Ratio'),
            ('quote_type', 'Quote Type (Text)', 'Instrument Type'),
            ('sector', 'Sector (Text)', 'Sector'),
            ('industry', 'Industry (Text)', 'Industry'),
        ],
    },
    'holding': [
        ('ticker', 'Ticker (Text)', 'Ticker'),
        ('quantity', 'Quantity (Number)', 'Shares Held'),
        ('total_investment', 'Total Investment (Number)', 'Total Investment'),
        ('purchase_date', 'Purchase Date (Date)', 'Purchase Date'),
    ],
}

# Map fields to expected data types for validation
FIELD_DATA_TYPES = {
    'ticker': 'string',
    'name': 'string',
    'price': 'decimal',
    'currency': 'string',
    'average_volume': 'decimal',
    'volume': 'decimal',
    'dividend_yield': 'decimal',
    'pe_ratio': 'decimal',
    'quote_type': 'string',
    'sector': 'string',
    'industry': 'string',
    'last_updated': 'date',
    'quantity': 'decimal',
    'total_investment': 'decimal',
    'purchase_date': 'date',
}
