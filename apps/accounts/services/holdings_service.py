from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType

from accounts.models.stocks import StockAccount
from assets.serializers.stocks import StockHoldingCreateSerializer
from schemas.models import SchemaColumnValue


def _assert_owns_account(user, account: StockAccount):
    # Ensures the account belongs to the requesting user's portfolio
    user_portfolio = user.profile.portfolio
    if account.stock_portfolio.portfolio_id != user_portfolio.id:
        raise ValidationError("Unauthorized account.")


def add_holding(account_id, holding_data, context):
    """
    Add a stock holding to a self-managed account.
    - Validates ownership (based on context['request'].user if present)
    - Ensures the account is self-managed
    - Passes `account` in serializer context (required by latest serializer)
    """
    try:
        account = StockAccount.objects.get(pk=account_id)
    except StockAccount.DoesNotExist:
        raise ValidationError("Account not found.")

    request = context.get("request")
    if request and hasattr(request, "user"):
        _assert_owns_account(request.user, account)

    if account.account_mode != "self_managed":
        raise ValidationError("Cannot add holdings to a managed account.")

    # Ensure the serializer receives the `account` in context
    ser_ctx = dict(context)
    ser_ctx["account"] = account

    serializer = StockHoldingCreateSerializer(data=holding_data, context=ser_ctx)
    serializer.is_valid(raise_exception=True)
    return serializer.save()


def edit_column_value(value_id, data, user):
    """
    Edit a column value for a stock holding, ensuring it belongs to the user.
    Uses ContentType for StockAccount (no hardcoded model string).
    """
    ct = ContentType.objects.get_for_model(StockAccount)
    try:
        value_obj = SchemaColumnValue.objects.get(
            pk=value_id,
            account_ct=ct,
            account__stock_portfolio__portfolio=user.profile.portfolio,
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
