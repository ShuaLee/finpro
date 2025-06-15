METALS_SCHEMA_CONFIG = {
    'asset': {
        'metal': {
            'data_type': 'string',
            'editable': False,
            'field_path': 'holding.preciousmetal.name'
        },
        'price': {
            'data_type': 'string',
            'editable': True,
            'field_path': 'holding.preciousmetal.price'
        }
    },
    'holding': {
        'quantity': {
            'data_type': 'decimal',
            'editable': True,
            'field_path': 'holding.weight_oz',
            'decimal_spaces': 4,
        },
        'purchase_price': {
            'data_type': 'decimal',
            'editable': True,
            'field_path': 'holding.purchase_price_per_oz',
            'decimal_spaces': 2,
        },
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
