from django.contrib.contenttypes.models import ContentType
from schemas.models import SchemaColumnValue
from schemas.services.schema_engine import HoldingSchemaEngine
from decimal import Decimal


def _cast_for_data_type(value, data_type: str):
    if value is None:
        return None
    if data_type == "decimal":
        return Decimal(str(value))


def recalc_calculated_for_holding(holding):
    """Recompute all calculated SCVs for a single holding."""
    schema = holding.get_active_schema()
    if not schema:
        return
    engine = HoldingSchemaEngine(holding, holding.get_asset_type())
    for col in schema.columns.filter(source="calculated"):
        engine.sync_column(col)


def apply_base_scv_to_holding(scv: SchemaColumnValue):
    """
    Push a base (source='holding') SCV value into the holding model field,
    validating via holding.clean()/full_clean(), then rely on holding.save()
    to re-sync SCVs + calculated columns.
    Returns the updated holding.
    """
    col = scv.column
    if col.source != "holding":
        return None

    model = scv.account_ct.model_class()
    holding = model.objects.filter(pk=scv.account_id).first()
    if not holding:
        return None

    # Coerce and validate on the model
    coerced = _cast_for_data_type(scv.value, col.data_type)
    setattr(holding, col.source_field, coerced)

    # This will run your model clean() (e.g. no negative quantity) and then
    # after commit your AssetHolding.save() will call engine.sync_all_columns()
    holding.save()

    return holding


def update_base_scv(holding, source_field: str, raw_value, mark_edited: bool = True):
    """
    Update (or create) a base SCV on a holding, then recompute calculated SCVs.
    Use this from API/views when user edits a base value.
    """
    schema = holding.get_active_schema()
    if not schema:
        return

    col = schema.columns.filter(
        source="holding", source_field=source_field).first()
    if not col:
        # If the schema doesn't have that column yet, nothing to persist (MVP rule).
        return

    ct = ContentType.objects.get_for_model(holding.__class__)
    val = _cast_for_data_type(raw_value, col.data_type)

    scv, _ = SchemaColumnValue.objects.update_or_create(
        column=col,
        account_ct=ct,
        account_id=holding.id,
        defaults={"value": val, "is_edited": bool(mark_edited)},
    )
    # After any base update, recompute all calculated cols for this holding
    recalc_calculated_for_holding(holding)


def recalc_after_base_scv_change(scv: SchemaColumnValue):
    """
    Call this after saving a base SCV from any path (admin/API).
    """
    col = scv.column
    if col.source == "calculated":
        return
    model = scv.account_ct.model_class()
    holding = model.objects.filter(pk=scv.account_id).first()
    if not holding:
        return
    recalc_calculated_for_holding(holding)


def get_asset_holding_model_map():
    # Lazy load to avoid circular imports
    # from metals.models import MetalHolding
    from assets.models import StockHolding

    return {
        "stockportfolio": StockHolding,
        # "metalportfolio": MetalHolding,
    }


def get_holdings_for_schema_object(content_type, object_id):
    model_map = get_asset_holding_model_map()
    model = model_map.get(content_type.model)
    if not model:
        return []

    if content_type.model == "stockportfolio":
        return model.objects.filter(
            self_managed_account__stock_portfolio_id=object_id
        )

    return []


def sync_schema_column_to_holdings(column):
    schema = column.schema
    holdings = get_holdings_for_schema_object(
        schema.content_type, schema.object_id)

    for holding in holdings:
        engine = HoldingSchemaEngine(holding, asset_type=holding.asset_type)
        engine.sync_column(column)
