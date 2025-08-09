from decimal import Decimal
from django.contrib.contenttypes.models import ContentType
from schemas.models import SchemaColumn, SchemaColumnValue


def _get_account_ct_and_id(account):
    return ContentType.objects.get_for_model(account.__class__), account.pk


def ensure_managed_account_scv_defaults(account):
    """
    For managed accounts: ensure account-scoped SCVs exist for:
      - currency: defaults to profile currency
      - current_value: defaults to 0.00
    """
    if not getattr(account, "is_managed", None) or not account.is_managed():
        return
    schema = account.active_schema
    if not schema:
        return

    account_ct, account_id = _get_account_ct_and_id(account)
    profile_currency = account.stock_portfolio.portfolio.profile.currency
    defaults = {
        "currency": str(profile_currency),
        "current_value": str(Decimal("0.00")),
    }

    for source_field, value_str in defaults.items():
        try:
            col = SchemaColumn.objects.get(
                schema=schema, source="custom", source_field=source_field
            )
        except SchemaColumn.DoesNotExist:
            continue  # user may have removed it
        scv, created = SchemaColumnValue.objects.get_or_create(
            column=col, account_ct=account_ct, account_id=account_id,
            defaults={"value": value_str, "is_edited": False},
        )
        if not created and (scv.value is None or scv.value == ""):
            scv.value = value_str
            scv.save(update_fields=["value"])
