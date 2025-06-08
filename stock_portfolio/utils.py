from .constants import SCHEMA_COLUMN_CONFIG


def resolve_field_path(instance, field_path: str):
    try:
        for attr in field_path.split('.'):
            instance = getattr(instance, attr, None)
            if instance is None:
                return None
        return instance
    except AttributeError:
        return None


def get_source_field_options():
    choices = []
    for source, fields in SCHEMA_COLUMN_CONFIG.items():
        for field, config in fields.items():
            label = field.replace('_', ' ').title() if field else "Custom"
            choices.append((source, field, label))
    return choices
