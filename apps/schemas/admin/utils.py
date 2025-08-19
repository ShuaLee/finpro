from django.db import models
from schemas.config import SCHEMA_CONFIG_REGISTRY


def build_builtin_choices_for_schema(schema):
    if not schema:
        return [], set(), None
    config = (SCHEMA_CONFIG_REGISTRY.get(schema.schema_type)
              or SCHEMA_CONFIG_REGISTRY.get(f"{schema.schema_type}_self_managed"))
    if not config:
        return [], set(), None

    existing = {
        f"{c.source}:{c.source_field}"
        for c in schema.columns.exclude(source__isnull=True).exclude(source_field__isnull=True)
    }

    choices, disabled = [], set()
    for group_label, fields in config.items():
        group = []
        for source_field, spec in fields.items():
            key = f"{group_label}:{source_field}"
            label = spec.get("title", source_field.replace("_", " ").title())
            group.append((key, label))
            if key in existing:
                disabled.add(key)
        if group:
            choices.append((group_label._meta.verbose_name.title(), group))
    return choices, disabled, config


def next_display_order(schema):
    return (schema.columns.aggregate(models.Max("display_order"))["display_order__max"] or 0) + 1
