from django.core.exceptions import ValidationError
from assets.serializers.stocks import StockHoldingCreateSerializer
from schemas.models import SchemaColumnValue


def add_holding(account_id, holding_data, context):
    """
    Add a stock holding to a self-managed account.
    """
    serializer = StockHoldingCreateSerializer(
        data=holding_data, context=context)
    serializer.is_valid(raise_exception=True)
    return serializer.save()


def edit_column_value(value_id, data, user):
    """
    Edit a column value for a stock holding, ensuring it belongs to the user.
    """
    try:
        value_obj = SchemaColumnValue.objects.get(
            pk=value_id,
            account_ct__model="selfmanagedaccount",  # hardcoded for now
            account__stock_portfolio__portfolio=user.profile.portfolio
        )
    except SchemaColumnValue.DoesNotExist:
        raise ValidationError("Column value not found or unauthorized.")

    # Reset override
    if data.get("is_edited") is False:
        value_obj.value = None
        value_obj.is_edited = False
        value_obj.save()
        return value_obj

    if "value" in data and data["value"] not in [None, ""]:
        value_obj.value = data["value"]
        value_obj.is_edited = True
        value_obj.save()
        return value_obj

    raise ValidationError("Invalid data for editing column value.")
