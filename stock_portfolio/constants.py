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
            'decimal_spaces': 2,
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
            'decimal_spaces': 4,
        },
        'purchase_price': {
            'data_type': 'decimal',
            'editable': True,
            'field_path': 'holding.purchase_price',
            'decimal_spaces': 2,
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
            'formula_required': False,
            'formula_method': 'get_current_value',
        },
        'value_in_profile_fx': {
            'data_type': 'decimal',
            'editable': False,
            'formula_required': True,
            'formula_method': 'get_current_value_profile_fx',
        },
        'unrealized_gain': {
            'data_type': 'decimal',
            'editable': False,
            'formula_required': True,
            'formula_method': 'get_unrealized_gain',
        },
        'unrealized_gain_profile_fx': {
            'data_type': 'decimal',
            'editable': False,
            'formula_required': True,
            'formula_method': 'get_unrealized_gain_profile_fx',
        },
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
        'title': 'Current Value',
        'data_type': 'decimal',
        'source': 'calculated',
        'source_field': 'current_value',
        'editable': False,
        'is_deletable': False,
        'formula': 'quantity * price',
    },
]
