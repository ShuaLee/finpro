FMP_FIELD_MAPPINGS = [
    # (model_field, api_field, source, data_type, required, default)
    ('name', 'name', 'quote', 'string', False, None),
    ('exchange', 'exchangeShortName', 'profile', 'string', False, None),
    ('is_adr', 'isAdr', 'profile', 'boolean', False, False),
    ('price', 'price', 'quote', 'decimal', True, None),
    ('volume', 'volume', 'quote', 'integer', False, None),
    ('average_volume', 'avgVolume', 'quote', 'integer', False, None),
    ('pe_ratio', 'pe', 'quote', 'decimal', False, None),
    ('sector', 'sector', 'profile', 'string', False, None),
    ('industry', 'industry', 'profile', 'string', False, None),
    ('currency', 'currency', 'profile', 'string', False, None),
    ('dividend_yield', None, 'profile', 'decimal', False, None),  # Calculated
    ('is_etf', 'isEtf', 'profile', 'boolean', False, None),
]
