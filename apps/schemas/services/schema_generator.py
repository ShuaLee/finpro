from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from schemas.models import SchemaColumn, SchemaColumnTemplate, Schema, SubPortfolioSchemaLink
import re


class SchemaGenerator:
    def __init__(self, subportfolio, schema_type: str):
        self.subportfolio = subportfolio
        self.schema_type = schema_type
        self.subportfolio_ct = ContentType.objects.get_for_model(subportfolio)
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
    # Template fetching
    # -------------------------------
    def _get_templates(self, account_model):
        account_model_ct = ContentType.objects.get_for_model(account_model)
        return SchemaColumnTemplate.objects.filter(
            account_model_ct=account_model_ct,
            schema_type=self.schema_type,
            is_default=True,
            is_system=True,
        ).order_by("display_order")

    # -------------------------------
    # Schema initialization
    # -------------------------------
    @transaction.atomic
    def initialize(self, account_model_map: dict, custom_schema_namer=None):
        """
        Build schema + columns for each account model in account_model_map.
        """
        for account_model, label in account_model_map.items():
            user_email = self.subportfolio.portfolio.profile.user.email
            schema_name = (
                custom_schema_namer(self.subportfolio, label)
                if custom_schema_namer
                else f"{user_email}'s {self.schema_type.title()} ({label}) Schema"
            )

            self.schema = Schema.objects.create(
                name=schema_name,
                schema_type=self.schema_type,
                content_type=self.subportfolio_ct,
                object_id=self.subportfolio.id,
            )

            # Load templates (fallback to custom_default if needed)
            templates = list(self._get_templates(account_model))
            if not templates and self.schema_type.startswith("custom:"):
                templates = list(
                    SchemaColumnTemplate.objects.filter(
                        account_model_ct=ContentType.objects.get_for_model(account_model),
                        schema_type="custom_default",
                        is_default=True,
                        is_system=True,
                    )
                )

            # 🚀 Use unified creation logic for all template columns
            for template in templates:
                self.add_from_template(template)

            # Link schema <-> subportfolio
            SubPortfolioSchemaLink.objects.update_or_create(
                subportfolio_ct=self.subportfolio_ct,
                subportfolio_id=self.subportfolio.id,
                account_model_ct=ContentType.objects.get_for_model(account_model),
                defaults={"schema": self.schema},
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
        template=None,
        is_editable=True,
        is_deletable=True,
        is_system=False,
        constraints=None,
        display_order=0,
    ):
        identifier = self.generate_identifier(title, prefix=source)

        return SchemaColumn.objects.create(
            schema=self.schema,
            title=title,
            data_type=data_type,
            source=source,
            source_field=source_field,
            identifier=identifier,
            formula=formula_obj,
            template=template if source != "custom" else None,
            is_editable=is_editable,
            is_deletable=is_deletable,
            is_system=is_system,
            constraints=constraints or {},
            display_order=display_order,
        )

    def add_from_template(self, template):
        return self.add_column(
            title=template.title,
            data_type=template.data_type,
            source=template.source,
            source_field=template.source_field,
            formula_obj=template.formula,
            template=template,
            is_editable=template.is_editable,
            is_deletable=template.is_deletable,
            is_system=template.is_system,
            constraints=template.constraints,
            display_order=template.display_order,
        )

    def add_custom_column(self, title: str, data_type: str, **kwargs):
        return self.add_column(title, data_type, "custom", **kwargs)

    def add_calculated_column(self, title: str, formula_obj, **kwargs):
        return self.add_column(title, "decimal", "calculated", formula_obj=formula_obj, **kwargs)
