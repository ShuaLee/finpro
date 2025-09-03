from django.contrib.contenttypes.models import ContentType
from decimal import Decimal, ROUND_DOWN
from schemas.models import SchemaColumnValue


def initialize_column_values(column):
    """
    Ensure all holdings/accounts in the schema have a value for this column.
    """
    schema = column.schema
    portfolio = schema.portfolio
    if not portfolio or not hasattr(portfolio, "holdings"):
        return

    holdings = portfolio.holdings.all()
    content_type = ContentType.objects.get_for_model(holdings.model)

    # Default value based on column type
    if column.data_type == "decimal":
        dp = int(column.constraints.get("decimal_places", 2))
        default_val = Decimal("0").quantize(
            Decimal(f"1.{'0'*dp}"), rounding=ROUND_DOWN)
    elif column.data_type == "string":
        default_val = "-"
    else:
        default_val = None

    for holding in holdings:
        SchemaColumnValue.objects.get_or_create(
            column=column,
            account_ct=content_type,
            account_id=holding.id,
            defaults={"value": default_val, "is_edited": False},
        )
