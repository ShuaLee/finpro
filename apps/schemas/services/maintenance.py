from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction

from schemas.models import SchemaColumn, SchemaColumnTemplate
from schemas.policies.default_schema_policy import DefaultSchemaPolicy
from schemas.services.engine import SchemaEngine


class SchemaMaintenanceService:
    """
    Reset/cleanup/resequence/repair operations.
    """

    @staticmethod
    @transaction.atomic
    def reset_to_default(schema):
        from schemas.services.bootstrap import SchemaBootstrapService
        from schemas.services.orchestration import SchemaOrchestrationService

        identifiers = DefaultSchemaPolicy.default_identifiers_for_account_type(
            schema.account_type
        )

        SchemaColumn.objects.filter(schema=schema).delete()

        if not identifiers:
            SchemaOrchestrationService.schema_changed(schema)
            return schema

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
    def account_deleted(account):
        from schemas.models import Schema

        portfolio = account.portfolio
        account_type = account.account_type

        still_exists = portfolio.accounts.filter(
            account_type=account_type).exists()
        if not still_exists:
            Schema.objects.filter(
                portfolio=portfolio,
                account_type=account_type,
            ).delete()

    @staticmethod
    def resequence(schema):
        engine = SchemaEngine(schema)
        engine.resequence()
