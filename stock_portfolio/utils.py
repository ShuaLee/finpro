from .constants import PREDEFINED_COLUMNS


def get_predefined_column_metadata(source, field):
    for col in PREDEFINED_COLUMNS.get(source, []):
        if col['field'] == field:
            return {
                'label': col['label'],
                'data_type': col['type']
            }
    return None
