from django.db import transaction
from schemas.models import StockPortfolioSchema, StockPortfolioSC
from schemas.constants import DEFAULT_STOCK_SCHEMA_COLUMNS
from schemas.services.schema_service import create_schema


@transaction.atomic
def add_default_columns(schema):
    """
    Adds default stock-specific columns to a schema.
    """
    for col_data in DEFAULT_STOCK_SCHEMA_COLUMNS:
        StockPortfolioSC.objects.create(schema=schema, **col_data)


@transaction.atomic
def initialize_stock_schema(stock_portfolio):
    """
    Creates a StockPortfolioSchema and its default columns.
    """
    schema = create_schema(StockPortfolioSchema, stock_portfolio)
    add_default_columns(schema)
    return schema


@transaction.atomic
def add_column_with_values(schema, col_data):
    """
    Add a new column to an existing schema and optionally initialize values.
    (Future feature for custom columns)
    """
    return StockPortfolioSC.objects.create(schema=schema, **col_data)
