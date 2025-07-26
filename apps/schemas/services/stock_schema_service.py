from django.db import transaction
from schemas.models import StockPortfolioSchema, StockPortfolioSC
from schemas.constants import STOCK_SCHEMA_COLUMNS_CATALOG
from schemas.services.schema_service import create_schema


def add_default_columns(schema):
    """
    Adds default stock-specific columns to a schema.
    """
    for col_data in STOCK_SCHEMA_COLUMNS_CATALOG:
        if col_data.get('is_default'):
            StockPortfolioSC.objects.create(schema=schema, **col_data)


def add_column_with_values(schema, col_data):
    """
    Add a new column to an existing schema and optionally initialize values.
    (Future feature for custom columns)
    """
    return StockPortfolioSC.objects.create(schema=schema, **col_data)


@transaction.atomic
def initialize_stock_schema(stock_portfolio):
    """
    Creates a StockPortfolioSchema and its default columns.
    """
    schema = create_schema(StockPortfolioSchema, stock_portfolio)
    add_default_columns(schema)
    return schema
