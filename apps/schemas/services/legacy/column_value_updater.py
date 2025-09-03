from django.db import transaction
from schemas.models import SchemaColumnValue
from schemas.services.calculated_column_engine import recalculate_calculated_columns


@transaction.atomic
def update_column_value(column_value: SchemaColumnValue, new_value: str):
    """
    Updates the value of a column and recalculates dependent calculated columns.
    """
    column = column_value.column

    if column.source == "calculated":
        raise ValueError("Cannot manually edit a calculated column.")

    if not column.editable:
        raise ValueError("This column is not editable.")

    if new_value in [None, ""]:
        column_value.value = None
        column_value.is_edited = False
    else:
        column_value.value = new_value
        column_value.is_edited = True

    column_value.save()

    # Trigger recalculation for dependent calculated columns
    schema = column.schema
    account = column_value.account
    recalculate_calculated_columns(schema, account)

    return column_value
