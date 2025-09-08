def get_default_for_type(data_type: str):
    """
    Return a sensible default value based on the given data_type.
    Supported types: decimal, integer, string, date, url.
    """
    defaults = {
        'decimal': 0,
        'integer': 0,
        'string': '',
        'date': None,  # Could later use timezone.now() if needed
        'url': '',
    }
    return defaults.get(data_type, None)


def format_quantity(holding):
    """
    Format holding quantity with the right decimals
    (delegates to schema constraints later).
    """
    return f"{holding.quantity.normalize()} {holding.asset.symbol}"


def asset_label(asset):
    """
    Return a user-friendly label for an asset.
    """
    return f"{asset.name} ({asset.symbol})"
