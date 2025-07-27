from django.db import transaction
from schemas.models import StockPortfolioSchema, StockPortfolioSC
from schemas.constants import STOCK_SCHEMA_COLUMNS_CATALOG
from schemas.services.schema_service import create_schema


@transaction.atomic
def add_default_columns(schema):
    """
    Adds all default stock-specific columns from catalog to the schema.
    """
    for col_data in STOCK_SCHEMA_COLUMNS_CATALOG:
        if col_data.get('is_default', False):
            StockPortfolioSC.objects.create(schema=schema, **col_data)


@transaction.atomic
def add_column_with_values(schema, col_data):
    """
    Add a new column to an existing schema.
    Future: initialize values for holdings.
    """
    return StockPortfolioSC.objects.create(schema=schema, **col_data)


@transaction.atomic
def initialize_stock_schema(stock_portfolio):
    """
    Creates a StockPortfolioSchema for the given portfolio and populates default columns.
    """
    schema = create_schema(StockPortfolioSchema, stock_portfolio)
    add_default_columns(schema)
    return schema
