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
