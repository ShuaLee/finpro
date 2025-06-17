def get_default_for_type(data_type: str):
    if data_type == 'decimal':
        return 0
    elif data_type == 'string':
        return ''
    return None