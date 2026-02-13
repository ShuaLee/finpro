from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.text import slugify

from schemas.models import (
    MasterConstraint,
    SchemaColumn,
    SchemaColumnValue,
    SchemaConstraint,
)
from schemas.models.account_column_visibility import AccountColumnVisibility
from schemas.policies.schema_column_deletion_policy import SchemaColumnDeletionPolicy
from schemas.services.queries import SchemaQueryService


class SchemaMutationService:
    """
    All schema writes: columns, values, constraints, visibility.
    """

    @staticmethod
    def _next_display_order(schema) -> int:
        return (schema.columns.aggregate(max=models.Max("display_order")).get("max") or 0) + 1

    @staticmethod
    def _ensure_unique_identifier(schema, base_identifier: str) -> str:
        existing = set(schema.columns.values_list("identifier", flat=True))
        identifier = base_identifier
        i = 1
        while identifier in existing:
            identifier = f"{base_identifier}_{i}"
            i += 1
        return identifier

    @staticmethod
    @transaction.atomic
    def add_system_column_from_template(*, schema, template_column):
        from schemas.services.bootstrap import SchemaBootstrapService
        return SchemaBootstrapService.add_system_column(
            schema=schema,
            template_column=template_column,
            recompute=True,
        )

    @staticmethod
    @transaction.atomic
    def add_custom_column(*, schema, title: str, data_type: str, identifier_override: str | None = None):
        from schemas.services.bootstrap import SchemaBootstrapService
        from schemas.services.orchestration import SchemaOrchestrationService

        if not title:
            raise ValidationError("Column title is required.")
        if not data_type:
            raise ValidationError("Column data_type is required.")

        base_identifier = slugify(identifier_override or title)
        if not base_identifier:
            raise ValidationError("Could not derive a valid identifier.")

        identifier = SchemaMutationService._ensure_unique_identifier(
            schema, base_identifier)

        column = SchemaColumn.objects.create(
            schema=schema,
            identifier=identifier,
            title=title,
            data_type=data_type,
            template=None,
            is_system=False,
            is_editable=True,
            is_deletable=True,
            display_order=SchemaMutationService._next_display_order(schema),
        )

        SchemaBootstrapService.create_constraints_from_master(
            column=column, overrides=None)
        SchemaBootstrapService.ensure_scvs_for_column(column)
        SchemaMutationService.initialize_visibility_for_schema_column(
            column=column)
        SchemaOrchestrationService.schema_changed(schema)

        return column

    @staticmethod
    @transaction.atomic
    def update_column(*, column: SchemaColumn, changed_fields: list[str]):
        from schemas.services.orchestration import SchemaOrchestrationService

        if "is_editable" in changed_fields and not column.is_editable:
            SchemaColumnValue.objects.filter(
                column=column,
                source=SchemaColumnValue.Source.USER,
            ).update(value=None, source=SchemaColumnValue.Source.SYSTEM)

        SchemaOrchestrationService.schema_changed(column.schema)
        return column

    @staticmethod
    @transaction.atomic
    def delete_column(column: SchemaColumn):
        from schemas.services.orchestration import SchemaOrchestrationService

        SchemaColumnDeletionPolicy.assert_deletable(column=column)
        schema = column.schema
        column.delete()
        SchemaOrchestrationService.schema_changed(schema)

    @staticmethod
    @transaction.atomic
    def update_constraint(*, constraint: SchemaConstraint, changed_fields: list[str]):
        from schemas.services.orchestration import SchemaOrchestrationService

        previous = SchemaConstraint.objects.get(pk=constraint.pk)

        if (
            "is_editable" in changed_fields
            and previous.is_editable
            and not constraint.is_editable
        ):
            master = MasterConstraint.objects.get(
                name=constraint.name,
                applies_to=constraint.applies_to,
            )
            default = master.default_value()

            if constraint.applies_to in ("decimal", "percent"):
                constraint.value_decimal = Decimal(
                    str(default if default is not None else 0))
                constraint.min_decimal = master.min_decimal
                constraint.max_decimal = master.max_decimal
            elif constraint.applies_to == "string":
                constraint.value_string = default
            elif constraint.applies_to == "boolean":
                constraint.value_boolean = bool(default)
            elif constraint.applies_to == "date":
                constraint.value_date = default
                constraint.min_date = master.min_date
                constraint.max_date = master.max_date

        constraint.full_clean()
        constraint.save()
        SchemaOrchestrationService.schema_changed(constraint.column.schema)
        return constraint

    @staticmethod
    @transaction.atomic
    def set_value(*, scv: SchemaColumnValue, raw_value):
        from schemas.services.orchestration import SchemaOrchestrationService

        column = scv.column
        holding = scv.holding
        asset = holding.asset if holding else None
        asset_type = asset.asset_type if asset else None

        behavior = column.behavior_for(asset_type) if asset_type else None

        if not column.is_editable:
            raise ValidationError("This column is not editable.")

        value = SchemaMutationService._validate_value(
            column=column, raw_value=raw_value)

        # Holding-backed editable column writes to source model field.
        if behavior and behavior.source == "holding":
            SchemaMutationService._write_to_source_field(
                root=holding,
                source_field=behavior.source_field,
                value=value,
            )
            scv.value = None
            scv.source = SchemaColumnValue.Source.SYSTEM
            scv.save(update_fields=["value", "source"])
        else:
            # User override path (asset/formula/constant/user)
            scv.value = str(value)
            scv.source = SchemaColumnValue.Source.USER
            scv.save(update_fields=["value", "source"])

        SchemaOrchestrationService.holding_changed(holding)
        return scv

    @staticmethod
    @transaction.atomic
    def revert_value(*, scv: SchemaColumnValue):
        from schemas.services.orchestration import SchemaOrchestrationService

        if scv.source != SchemaColumnValue.Source.USER:
            return scv

        scv.value = None
        scv.source = SchemaColumnValue.Source.SYSTEM
        scv.save(update_fields=["value", "source"])

        if scv.holding:
            SchemaOrchestrationService.holding_changed(scv.holding)

        return scv

    @staticmethod
    def _validate_value(*, column, raw_value):
        enum_constraint = column.constraints.filter(name="enum").first()
        if enum_constraint:
            allowed = SchemaQueryService.resolve_enum_values(
                enum_constraint, column=column)
            if allowed and raw_value not in allowed:
                raise ValidationError(
                    f"Invalid value '{raw_value}'. Allowed: {allowed}")

        try:
            if column.data_type == "decimal":
                value = Decimal(str(raw_value))
            elif column.data_type == "percent":
                raw = str(raw_value).strip()
                if raw.endswith("%"):
                    raw = raw[:-1].strip()
                value = Decimal(raw) / Decimal("100")
            elif column.data_type == "boolean":
                value = SchemaMutationService._cast_boolean(raw_value)
            elif column.data_type == "date":
                value = raw_value
            else:
                value = str(raw_value)
        except Exception:
            raise ValidationError(
                f"Invalid value for data_type '{column.data_type}'.")

        for constraint in column.constraints.all():
            constraint.validate(value)

        return value

    @staticmethod
    def _cast_boolean(raw):
        if isinstance(raw, bool):
            return raw
        val = str(raw).strip().lower()
        if val in ("true", "1", "yes"):
            return True
        if val in ("false", "0", "no"):
            return False
        raise ValidationError("Invalid boolean value.")

    @staticmethod
    def _write_to_source_field(*, root, source_field: str | None, value):
        if not source_field:
            raise ValidationError(
                "Missing source_field for holding-backed column.")

        target = root
        parts = source_field.split("__")
        for part in parts[:-1]:
            target = getattr(target, part, None)
            if target is None:
                raise ValidationError(
                    f"Invalid source_field path '{source_field}'.")

        setattr(target, parts[-1], value)
        target.save()

    @staticmethod
    def initialize_visibility_for_schema_column(*, column):
        accounts = column.schema.portfolio.accounts.filter(
            account_type=column.schema.account_type
        )

        AccountColumnVisibility.objects.bulk_create(
            [
                AccountColumnVisibility(
                    account=account, column=column, is_visible=True)
                for account in accounts
            ],
            ignore_conflicts=True,
        )

    @staticmethod
    def initialize_visibility_for_account(*, account):
        from schemas.services.bootstrap import SchemaBootstrapService

        schema = SchemaBootstrapService.ensure_for_account(account)

        AccountColumnVisibility.objects.bulk_create(
            [
                AccountColumnVisibility(
                    account=account, column=column, is_visible=True)
                for column in schema.columns.all()
            ],
            ignore_conflicts=True,
        )

    @staticmethod
    def set_visibility(*, account, column, is_visible: bool):
        AccountColumnVisibility.objects.update_or_create(
            account=account,
            column=column,
            defaults={"is_visible": is_visible},
        )
