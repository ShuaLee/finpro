from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from schemas.models import Schema, SchemaColumn, SubPortfolioSchemaLink, SchemaColumnTemplate
import re


def get_schema_column_templates(schema_type: str, account_model_class):
    """
    Fetches default system schema column templates for a given schema_type and account model.
    """
    account_model_ct = ContentType.objects.get_for_model(account_model_class)

    return SchemaColumnTemplate.objects.filter(
        account_model_ct=account_model_ct,
        schema_type=schema_type,
        is_default=True,
        is_system=True,
    ).order_by("display_order")


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
            custom_schema_namer(subportfolio, label)
            if custom_schema_namer else f"{user_email}'s {schema_type.title()} ({label}) Schema"
        )

        schema = Schema.objects.create(
            name=schema_name,
            schema_type=schema_type,
            content_type=subportfolio_ct,
            object_id=subportfolio.id,
        )

        # 1) Try exact templates
        templates = list(get_schema_column_templates(
            schema_type, account_model_class=account_model))

        # 2) If custom:* and none found, fall back to 'custom_default'
        if not templates and schema_type.startswith("custom:"):
            templates = list(get_schema_column_templates(
                "custom_default", account_model_class=account_model))

        # 3) Create columns from whichever template set we have
        for template in templates:
            create_kwargs = dict(
                schema=schema,
                source=template.source,
                source_field=template.source_field,
                title=template.title,
                data_type=template.data_type,
                field_path=template.field_path,
                is_editable=template.is_editable,
                is_deletable=template.is_deletable,
                is_system=template.is_system,
                constraints=template.constraints,
                display_order=template.display_order,
                formula=template.formula,
            )

            # ✅ Only attach template if not a custom column
            if template.source != "custom":
                create_kwargs["template"] = template

            # identifier will be auto-generated in SchemaColumn.clean()
            SchemaColumn.objects.create(**create_kwargs)

        SubPortfolioSchemaLink.objects.update_or_create(
            subportfolio_ct=subportfolio_ct,
            subportfolio_id=subportfolio.id,
            account_model_ct=ContentType.objects.get_for_model(account_model),
            defaults={"schema": schema}
        )


# ---------------------------------------------------------------------------------- #


def _generate_identifier(schema: Schema, title: str, prefix: str = "col") -> str:
    """
    Generate a unique snake_case identifier for a column within a schema.
    """
    base = re.sub(r'[^a-z0-9_]', '_', title.lower())
    base = re.sub(r'_+', '_', base).strip('_') or prefix
    proposed = base
    counter = 1

    while SchemaColumn.objects.filter(schema=schema, identifier=proposed).exists():
        counter += 1
        proposed = f"{base}_{counter}"

    return proposed


@transaction.atomic
def add_custom_column(schema: Schema, title: str, data_type: str, is_editable=True, is_deletable=True):
    """
    Adds a new custom (user-defined) column to the schema.
    Ensures identifier is set and unique within the schema.
    """
    identifier = _generate_identifier(schema, title, prefix="custom_field")

    return SchemaColumn.objects.create(
        schema=schema,
        title=title,
        data_type=data_type,
        source="custom",
        identifier=identifier,
        is_editable=is_editable,
        is_deletable=is_deletable,
    )


def extract_variables_from_formula(formula: str):
    """
    Extracts all variable names from a formula expression.
    e.g., "(quantity * price) / pe_ratio" -> ['quantity', 'price', 'pe_ratio']
    """
    return re.findall(r'[a-zA-Z_]\w*', formula)


@transaction.atomic
def add_calculated_column(schema: Schema, title: str, formula_obj):
    """
    Adds a calculated column to the schema.
    Also creates any missing referenced variables as editable custom fields.
    `formula_obj`: Formula instance
    """
    variables = formula_obj.dependencies or []
    existing_identifiers = [col.identifier for col in schema.columns.all() if col.identifier]

    for var in variables:
        if var not in existing_identifiers:
            SchemaColumn.objects.create(
                schema=schema,
                title=var.replace("_", " ").title(),
                data_type="decimal",
                source="custom",
                identifier=var,  # ✅ treat formula deps as identifiers directly
                is_editable=True,
                is_deletable=True,
            )
