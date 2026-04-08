import json
from datetime import date
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError


def serialize_typed_value(*, data_type: str, value):
    if value is None:
        return None

    if data_type == "decimal":
        try:
            return str(Decimal(str(value)))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValidationError("Invalid decimal value.") from exc

    if data_type == "percent":
        raw = str(value).strip()
        if raw.endswith("%"):
            raw = raw[:-1].strip()
        try:
            return str(Decimal(raw))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValidationError("Invalid percent value.") from exc

    if data_type == "boolean":
        if isinstance(value, bool):
            return "true" if value else "false"
        raw = str(value).strip().lower()
        if raw in {"true", "1", "yes"}:
            return "true"
        if raw in {"false", "0", "no"}:
            return "false"
        raise ValidationError("Invalid boolean value.")

    if data_type == "date":
        if isinstance(value, date):
            return value.isoformat()
        raw = str(value).strip()
        try:
            return date.fromisoformat(raw).isoformat()
        except ValueError as exc:
            raise ValidationError("Invalid date value.") from exc

    if data_type == "json":
        try:
            return json.dumps(value)
        except TypeError as exc:
            raise ValidationError("Invalid JSON value.") from exc

    return str(value).strip()


def parse_typed_value(*, data_type: str, raw_value):
    if raw_value in (None, ""):
        return None

    if data_type == "decimal":
        return Decimal(str(raw_value))

    if data_type == "percent":
        return Decimal(str(raw_value))

    if data_type == "boolean":
        return str(raw_value).strip().lower() == "true"

    if data_type == "date":
        return date.fromisoformat(str(raw_value))

    if data_type == "json":
        return json.loads(raw_value)

    return str(raw_value)
