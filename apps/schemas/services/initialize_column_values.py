from django.contrib.contenttypes.models import ContentType
from decimal import Decimal, ROUND_DOWN
from schemas.models import SchemaColumnValue, SchemaColumn


def initialize_column_values(column: SchemaColumn, accounts=None):
    """
    Ensure all holdings/accounts in the schema have a value for this column.
    Defaults: 0 (with decimal_places) for decimals, "-" for strings, None otherwise.
    """
    schema = column.schema
    portfolio = schema.portfolio

    # Fallback if no accounts explicitly passed
    if accounts is None:
        if not portfolio or not hasattr(portfolio, "holdings"):
            return
        accounts = portfolio.holdings.all()

    if not accounts:
        return

    # Default value logic
    if column.data_type == "decimal":
        dp = int(column.constraints.get("decimal_places", 2))
        default_val = Decimal("0").quantize(
            Decimal(f"1.{'0'*dp}"), rounding=ROUND_DOWN
        )
    elif column.data_type == "string":
        default_val = "-"
    else:
        default_val = None

    ct = ContentType.objects.get_for_model(accounts.model)

    for account in accounts:
        SchemaColumnValue.objects.get_or_create(
            column=column,
            account_ct=ct,
            account_id=account.id,
            defaults={"value": default_val, "is_edited": False},
        )