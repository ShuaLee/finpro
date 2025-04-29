PREDEFINED_COLUMNS = {
    'stock': [
        {'field': 'ticker', 'label': 'Ticker', 'type': 'string'},
        {'field': 'last_proce', 'label': 'Price', 'type': 'number'},
    ],
    'holding': [
        {'field': 'purchase_price', 'label': 'Purchase Price', 'type': 'number'},
        {'field': 'shares', 'label': 'Shares Owned', 'type': 'number'},
    ],
    'custom': [
        {'field': None, 'label': 'Custom: Number', 'type': 'number'},
        {'field': None, 'label': 'Custom: Text', 'type': 'string'},
    ]
}
"""
ChatGPT says: 
    If your custom columns are truly free-form, meaning users define:

    The name

    The type

    ...then hardcoding 'custom' options inside PREDEFINED_COLUMNS could feel artificial. You might just handle those as:

    "Add Custom Column" button

    Pop-up form asking for name + type
"""
