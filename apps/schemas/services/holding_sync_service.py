from apps.schemas.services.schema_engine import HoldingSchemaEngine


def get_asset_holding_model_map():
    # Lazy load to avoid circular imports
    from assets.models import StockHolding
    # from metals.models import MetalHolding

    return {
        "stockportfolio": StockHolding,
        # "metalportfolio": MetalHolding,
    }


def get_holdings_for_schema_object(content_type, object_id):
    model_map = get_asset_holding_model_map()
    model = model_map.get(content_type.model)
    if not model:
        return []

    return model.objects.filter(account__sub_portfolio=object_id)


def sync_schema_column_to_holdings(column):
    schema = column.schema
    holdings = get_holdings_for_schema_object(
        schema.content_type, schema.object_id)

    for holding in holdings:
        engine = HoldingSchemaEngine(holding, asset_type=holding.asset_type)
        engine.sync_column(column)
