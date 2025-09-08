from django.db import transaction, models
from schemas.models import SchemaColumn, Schema
from core.types import get_schema_config_for_account_type
import re


class SchemaGenerator:
    def __init__(self, subportfolio, schema_type: str):
        self.subportfolio = subportfolio
        self.schema_type = schema_type
        self.schema = None

    # -------------------------------
    # Identifier generation
    # -------------------------------
    def generate_identifier(self, title: str, prefix: str = "col") -> str:
        base = re.sub(r'[^a-z0-9_]', '_', title.lower())
        base = re.sub(r'_+', '_', base).strip('_') or prefix
        proposed = base
        counter = 1

        while SchemaColumn.objects.filter(schema=self.schema, identifier=proposed).exists():
            counter += 1
            proposed = f"{base}_{counter}"

        return proposed

    # -------------------------------
    # Schema initialization
    # -------------------------------
    @transaction.atomic
    def initialize(self, account_types: list[str], custom_schema_namer=None):
        """
        Build schema + system columns for each account type using DOMAIN_TYPE_REGISTRY.
        """
        for account_type in account_types:
            user_email = self.subportfolio.portfolio.profile.user.email
            schema_name = (
                custom_schema_namer(self.subportfolio, account_type)
                if custom_schema_namer
                else f"{user_email}'s {self.schema_type.title()} ({account_type}) Schema"
            )

            self.schema, _ = Schema.objects.update_or_create(
                subportfolio=self.subportfolio,
                account_type=account_type,
                defaults={
                    "name": schema_name,
                    "schema_type": self.schema_type,
                },
            )

            # 🔍 Fetch config from central domain registry
            config = get_schema_config_for_account_type(account_type)
            if not config:
                raise ValueError(f"No schema config found for account type '{account_type}'")

            # 🧱 Add columns defined in config
            for source, field_defs in config.items():
                for source_field, col_def in field_defs.items():
                    if col_def.get("is_default"):
                        self.add_column(
                            title=col_def["title"],
                            data_type=col_def["data_type"],
                            source=source,
                            source_field=source_field,
                            formula_obj=None,  # Hook formula resolution later
                            is_editable=col_def.get("is_editable", True),
                            is_deletable=col_def.get("is_deletable", True),
                            is_system=col_def.get("is_system", False),
                            constraints=col_def.get("constraints", {}),
                            display_order=col_def.get("display_order", 0),
                        )

        return self.schema

    # -------------------------------
    # Column creation (core + wrappers)
    # -------------------------------
    def add_column(
        self,
        title: str,
        data_type: str,
        source: str,
        *,
        source_field: str = None,
        formula_obj=None,
        is_editable=True,
        is_deletable=True,
        is_system=False,
        constraints=None,
        display_order=0,
    ):
        identifier = self.generate_identifier(title, prefix=source)

        if display_order is None:
            max_order = (
                SchemaColumn.objects.filter(schema=self.schema)
                .aggregate(models.Max("display_order"))["display_order__max"]
                or 0
            )
            display_order = max_order + 1

        return SchemaColumn.objects.create(
            schema=self.schema,
            title=title,
            data_type=data_type,
            source=source,
            source_field=source_field,
            identifier=identifier,
            formula=formula_obj,
            is_editable=is_editable,
            is_deletable=is_deletable,
            is_system=is_system,
            constraints=constraints or {},
            display_order=display_order,
        )

    def add_custom_column(self, title: str, data_type: str, **kwargs):
        return self.add_column(title, data_type, "custom", **kwargs)

    def add_calculated_column(self, title: str, formula_obj, **kwargs):
        return self.add_column(title, "decimal", "calculated", formula_obj=formula_obj, **kwargs)
