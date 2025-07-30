from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from schemas.models import Schema, SchemaColumn
from schemas.config.utils import get_schema_column_defaults
import re


@transaction.atomic
def initialize_stock_schema(stock_portfolio, name=None):
    """
    Creates a schema for a StockPortfolio and populates it with default columns from config.
    The schema name will default to: "<email>'s <SubPortfolioType> Schema"
    """
    if name is None:
        email = stock_portfolio.portfolio.profile.user.email
        portfolio_type = stock_portfolio.__class__.__name__
        name = f"{email}'s {portfolio_type} Schema"
        
    schema = Schema.objects.create(
        name=name,
        schema_type="stock",
        content_type=ContentType.objects.get_for_model(stock_portfolio),
        object_id=stock_portfolio.id,
    )

    default_columns = get_schema_column_defaults("stock")

    for col_data in default_columns:
        SchemaColumn.objects.create(schema=schema, **col_data)

    return schema


@transaction.atomic
def add_custom_column(schema: Schema, title: str, data_type: str, editable=True, is_deletable=True):
    """
    Adds a new custom (user-defined) column to the schema.
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
    """
    Extracts all variable names from a formula expression.
    e.g., "(quantity * price) / pe_ratio" -> ['quantity', 'price', 'pe_ratio']
    """
    return re.findall(r'[a-zA-Z_]\w*', formula)


@transaction.atomic
def add_calculated_column(schema: Schema, title: str, formula: str):
    """
    Adds a calculated column to the schema.
    Also creates any missing referenced variables as editable custom fields.
    """
    variables = extract_variables_from_formula(formula)
    existing_fields = [
        col.source_field.lower() if col.source_field else col.title.lower().replace(" ", "_")
        for col in schema.columns.all()
    ]

    for var in variables:
        if var.lower() not in existing_fields:
            SchemaColumn.objects.create(
                schema=schema,
                title=var.replace("_", " ").title(),
                data_type="decimal",
                source="custom",
                source_field=var,
                editable=True,
                is_deletable=True
            )

    return SchemaColumn.objects.create(
        schema=schema,
        title=title,
        data_type="decimal",
        source="calculated",
        formula_expression=formula,
        editable=False,
        is_deletable=True,
    )
