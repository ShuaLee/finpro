from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from schemas.models.core import Schema, SchemaColumn
from schemas.config import STOCK_DEFAULT_COLUMNS
import re


@transaction.atomic
def initialize_stock_schema(stock_portfolio, name="Default Stock Schema"):
    """
    Creates a schema for a StockPortfolio and populates it with default columns.
    """
    schema = Schema.objects.create(
        name=name,
        schema_type="stock",
        content_type=ContentType.objects.get_for_model(stock_portfolio),
        object_id=stock_portfolio.id,
    )

    for col_data in STOCK_DEFAULT_COLUMNS:
        SchemaColumn.objects.create(schema=schema, **col_data)

    return schema


@transaction.atomic
def add_custom_column(schema: Schema, title: str, data_type: str, editable=True, is_deletable=True):
    """
    Adds a new custom column to the schema.
    """
    return SchemaColumn.objects.create(
        schema=schema,
        title=title,
        data_type=data_type,
        source="custom",
        editable=editable,
        is_deletable=is_deletable,
    )


def extract_variables_from_formula(formula: str):
    return re.findall(r'[a-zA-Z_]\w*', formula)


@transaction.atomic
def add_calculated_column(schema: Schema, title: str, formula: str):
    """
    Adds a calculated column to the schema and ensures referenced variables exist.
    """
    variables = extract_variables_from_formula(formula)
    existing_titles = [col.title.lower().replace(" ", "_")
                       for col in schema.columns.all()]

    for var in variables:
        if var.lower() not in existing_titles:
            SchemaColumn.objects.create(
                schema=schema,
                title=var.replace("_", " ").title(),
                data_type="decimal",
                source="custom",
                editable=True,
                is_deletable=True
            )

    return SchemaColumn.objects.create(
        schema=schema,
        title=title,
        data_type="decimal",
        source="calculated",
        formula=formula,
        editable=False,
        is_deletable=True
    )
