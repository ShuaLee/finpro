from schemas.services.schema_engine import HoldingSchemaEngine


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
