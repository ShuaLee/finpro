from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from schemas.models import Schema, SchemaColumn, SubPortfolioSchemaLink
from schemas.config.utils import get_schema_column_defaults
import re


@transaction.atomic
def initialize_asset_schema(subportfolio, schema_type: str, account_model_map: dict, custom_schema_namer=None):
    """
    Generic initializer for any asset subportfolio schema (e.g., stock, crypto, metals).
    `account_model_map`: {AccountModelClass: "Label"}
    `schema_type`: str used in Schema.schema_type
    `custom_schema_namer`: optional callable for overriding schema name
    """
    subportfolio_ct = ContentType.objects.get_for_model(subportfolio)

    for account_model, label in account_model_map.items():
        user_email = subportfolio.portfolio.profile.user.email

        schema_name = (
            custom_schema_namer(
                subportfolio, label) if custom_schema_namer else f"{user_email}'s {schema_type.title()} ({label}) Schema"
        )

        schema = Schema.objects.create(
            name=schema_name,
            schema_type=schema_type,
            content_type=subportfolio_ct,
            object_id=subportfolio.id,
        )

        default_columns = get_schema_column_defaults(
            schema_type, account_model_class=account_model
        )

        for col_data in default_columns:
            SchemaColumn.objects.create(schema=schema, **col_data)

        SubPortfolioSchemaLink.objects.update_or_create(
            subportfolio_ct=subportfolio_ct,
            subportfolio_id=subportfolio.id,
            account_model_ct=ContentType.objects.get_for_model(account_model),
            defaults={"schema": schema}
        )


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
