from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.core.management import call_command

from schemas.models import (
    MasterConstraint,
    Schema,
    SchemaColumn,
    SchemaColumnTemplate,
    SchemaColumnValue,
    SchemaConstraint,
)
from schemas.models.schema_column_asset_behaviour import SchemaColumnAssetBehaviour
from schemas.policies.default_schema_policy import DefaultSchemaPolicy
from schemas.services.formula_bridge import (
    formula_dependencies,
    is_implicit_identifier,
)
from assets.models.core import AssetType


class SchemaBootstrapService:
    """
    Schema creation, expansion, and initial structural wiring.
    """

    @staticmethod
    @transaction.atomic
    def ensure_for_account(account):
        if account.schema_id:
            return account.schema

        allowed_asset_types = list(account.allowed_asset_types.all()[:2])
        if len(allowed_asset_types) == 1:
            return SchemaBootstrapService.initialize(
                portfolio=account.portfolio,
                asset_type=allowed_asset_types[0],
            )

        schema = Schema.objects.filter(
            portfolio=account.portfolio,
            account_type=account.account_type,
            asset_type__isnull=True,
        ).first()
        if schema:
            return schema

        return SchemaBootstrapService.initialize(
            portfolio=account.portfolio,
            account_type=account.account_type,
        )

    @staticmethod
    @transaction.atomic
    def initialize(*, portfolio, account_type=None, asset_type=None):
        from schemas.services.orchestration import SchemaOrchestrationService

        if not account_type and not asset_type:
            raise ValidationError("Either account_type or asset_type is required.")

        lookup = {"portfolio": portfolio}
        if asset_type is not None:
            lookup["asset_type"] = asset_type
        elif account_type is not None:
            lookup["account_type"] = account_type
        else:
            lookup["account_type__isnull"] = True

        schema = Schema.objects.filter(**lookup).first()
        if schema:
            return schema

        schema = Schema.objects.create(
            portfolio=portfolio,
            account_type=None if asset_type is not None else account_type,
            asset_type=asset_type,
        )

        identifiers = (
            DefaultSchemaPolicy.default_identifiers_for_asset_type(asset_type)
            if asset_type is not None
            else DefaultSchemaPolicy.default_identifiers_for_account_type(account_type)
        )
        if not identifiers:
            return schema

        SchemaBootstrapService.ensure_system_catalog_seeded()

        templates = SchemaColumnTemplate.objects.filter(
            identifier__in=identifiers,
            is_system=True,
        )

        found = {t.identifier for t in templates}
        missing = set(identifiers) - found
        if missing:
            raise ValidationError(
                f"Missing system templates: {sorted(missing)}")

        by_identifier = {t.identifier: t for t in templates}

        for identifier in identifiers:
            SchemaBootstrapService.add_system_column(
                schema=schema,
                template_column=by_identifier[identifier],
                recompute=False,
            )

        SchemaOrchestrationService.schema_changed(schema)
        return schema

    @staticmethod
    def ensure_system_catalog_seeded():
        if SchemaColumnTemplate.objects.filter(is_system=True).exists():
            return

        for asset_type_name in (
            "Equity",
            "Cryptocurrency",
            "Commodity",
            "Precious Metal",
            "Real Estate",
        ):
            AssetType.objects.get_or_create(name=asset_type_name, created_by=None)

        call_command("seed_master_constraints")
        call_command("seed_schema_column_categories")
        call_command("seed_formulas")
        call_command("seed_system_column_catalog")

    @staticmethod
    @transaction.atomic
    def add_system_column(*, schema, template_column: SchemaColumnTemplate, recompute: bool = True):
        from schemas.services.orchestration import SchemaOrchestrationService

        if not template_column.is_system:
            raise ValidationError(
                "Only system template columns may be expanded.")

        existing = schema.columns.filter(
            identifier=template_column.identifier).first()
        if existing:
            return existing

        # Expand formula dependencies first.
        for t_behavior in template_column.behaviours.select_related(
            "asset_type"
        ):
            if t_behavior.source != "formula":
                continue

            if not t_behavior.formula_identifier:
                raise ValidationError(
                    f"Template '{template_column.identifier}' has formula behavior without formula_identifier."
                )

            dependencies = formula_dependencies(
                identifier=t_behavior.formula_identifier,
                asset_type=t_behavior.asset_type,
            )
            for dep_identifier in dependencies:
                if is_implicit_identifier(dep_identifier):
                    continue

                dep_template = SchemaColumnTemplate.objects.filter(
                    identifier=dep_identifier,
                    is_system=True,
                ).first()

                if not dep_template:
                    raise ValidationError(
                        f"Missing dependency template '{dep_identifier}' "
                        f"required by formula '{formula.identifier}'."
                    )

                SchemaBootstrapService.add_system_column(
                    schema=schema,
                    template_column=dep_template,
                    recompute=False,
                )

        max_order = (
            schema.columns.aggregate(max=models.Max(
                "display_order")).get("max") or 0
        )

        is_editable = template_column.behaviours.filter(
            source__in=["holding", "user"]
        ).exists()

        column = SchemaColumn.objects.create(
            schema=schema,
            identifier=template_column.identifier,
            title=template_column.title,
            data_type=template_column.data_type,
            template=template_column,
            is_system=True,
            is_editable=is_editable,
            is_deletable=False,
            display_order=max_order + 1,
        )

        for t_behavior in template_column.behaviours.all():
            SchemaColumnAssetBehaviour.objects.create(
                column=column,
                asset_type=t_behavior.asset_type,
                source=t_behavior.source,
                formula_identifier=t_behavior.formula_identifier,
                source_field=t_behavior.source_field,
                constant_value=t_behavior.constant_value,
                is_override=False,
            )

        SchemaBootstrapService.create_constraints_from_master(
            column=column,
            overrides=template_column.constraint_overrides or {},
        )
        SchemaBootstrapService.ensure_scvs_for_column(column)

        from schemas.services.mutations import SchemaMutationService
        SchemaMutationService.initialize_visibility_for_schema_column(
            column=column)

        if recompute:
            SchemaOrchestrationService.schema_changed(schema)

        return column

    @staticmethod
    def create_constraints_from_master(*, column, overrides=None):
        overrides = overrides or {}

        masters = MasterConstraint.objects.filter(applies_to=column.data_type)
        for master in masters:
            raw_value = overrides.get(master.name, master.default_value())

            # Ensure decimal/percent constraints always have a value.
            if master.applies_to in ("decimal", "percent") and raw_value is None:
                raw_value = Decimal("0")

            defaults = {
                "label": master.label,
                "source": SchemaConstraint.Source.SYSTEM,
                "applies_to": master.applies_to,
                "is_editable": False,
                "min_decimal": master.min_decimal,
                "max_decimal": master.max_decimal,
                "min_date": master.min_date,
                "max_date": master.max_date,
            }

            if master.applies_to in ("decimal", "percent"):
                defaults["value_decimal"] = Decimal(str(raw_value))
            elif master.applies_to == "boolean":
                defaults["value_boolean"] = bool(raw_value)
            elif master.applies_to == "date":
                defaults["value_date"] = raw_value
            else:
                defaults["value_string"] = None if raw_value is None else str(
                    raw_value)

            SchemaConstraint.objects.get_or_create(
                column=column,
                name=master.name,
                defaults=defaults,
            )

    @staticmethod
    def ensure_scvs_for_column(column):
        from accounts.models import Holding

        schema = column.schema
        holdings = list(
            Holding.objects.filter(account__portfolio=schema.portfolio).select_related(
                "account",
                "asset",
                "asset__asset_type",
            )
        )

        holding_ids = [
            holding.id
            for holding in holdings
            if holding.active_schema and holding.active_schema.id == schema.id
        ]

        existing_holding_ids = set(
            SchemaColumnValue.objects.filter(
                column=column,
                holding_id__in=holding_ids,
            ).values_list("holding_id", flat=True)
        )

        to_create = []
        for holding in holdings:
            active_schema = holding.active_schema
            if not active_schema or active_schema.id != schema.id:
                continue
            if holding.id not in existing_holding_ids:
                to_create.append(
                    SchemaColumnValue(
                        column=column,
                        holding=holding,
                        value=None,
                        source=SchemaColumnValue.Source.SYSTEM,
                    )
                )

        if to_create:
            SchemaColumnValue.objects.bulk_create(to_create)
