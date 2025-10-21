from django.db import transaction, models
from schemas.models.schema import Schema, SchemaColumn
from schemas.utils import normalize_constraints
from core.types import get_domain_meta
import re

import logging

logger = logging.getLogger(__name__)


class SchemaGenerator:
    def __init__(self, portfolio, domain_type: str):
        self.portfolio = portfolio
        self.domain_type = domain_type
        self.schema = None

    # -------------------------------
    # Identifier generation
    # -------------------------------
    def generate_identifier(self, title: str, prefix: str = "col") -> str:
        base = re.sub(r"[^a-z0-9_]", "_", title.lower())
        base = re.sub(r"_+", "_", base).strip("_") or prefix
        proposed = base
        counter = 1

        while SchemaColumn.objects.filter(
            schema=self.schema, identifier=proposed
        ).exists():
            counter += 1
            proposed = f"{base}_{counter}"

        return proposed

    # -------------------------------
    # Schema initialization
    # -------------------------------
    @transaction.atomic
    def initialize(self, custom_schema_namer=None):
        """
        Build one schema per account_type in this portfolio’s domain.
        Example: stock portfolio → [self-managed schema, managed schema].
        """
        logger.debug(
            f"🛠 Initializing schema for portfolio={self.portfolio.id}, domain={self.domain_type}")

        try:
            domain_meta = get_domain_meta(self.domain_type)
            logger.debug(
                f"✅ Fetched domain meta for {self.domain_type}: {domain_meta}")

            account_types = domain_meta.get("account_types", [])
            schema_config = domain_meta.get("schema_config")

            if not account_types:
                logger.error(
                    f"❌ No account types registered for domain {self.domain_type}")
                raise ValueError(
                    f"No account types registered for domain {self.domain_type}")

            if not schema_config:
                logger.error(
                    f"❌ No schema config found for domain {self.domain_type}")
                raise ValueError(
                    f"No schema config found for domain {self.domain_type}")

            for account_type in account_types:
                user_email = self.portfolio.portfolio.profile.user.email
                schema_name = (
                    custom_schema_namer(self.portfolio, account_type)
                    if custom_schema_namer
                    else f"{user_email}'s {self.domain_type.title()} ({account_type}) Schema"
                )

                logger.debug(
                    f"📄 Creating/updating schema for account_type={account_type}, name={schema_name}")

                # 🚀 Ensure one schema per (portfolio, account_type)
                self.schema, created = Schema.objects.update_or_create(
                    portfolio=self.portfolio,
                    account_type=account_type,
                    defaults={
                        "domain_type": self.domain_type,
                        "name": schema_name,
                        "schema_type": "default",
                    },
                )
                logger.debug(
                    f"✅ {'Created' if created else 'Updated'} schema: {self.schema.id}")

                # 🧱 Add columns
                for source, field_defs in schema_config.items():
                    for source_field, col_def in field_defs.items():
                        if col_def.get("is_default"):
                            logger.debug(
                                f"➕ Adding column: {col_def['title']} from source={source}")
                            self.add_column(
                                title=col_def["title"],
                                data_type=col_def["data_type"],
                                source=source,
                                source_field=source_field,
                                formula_obj=None,
                                is_editable=col_def.get("is_editable", True),
                                is_deletable=col_def.get("is_deletable", True),
                                is_system=col_def.get("is_system", False),
                                constraints=col_def.get("constraints", {}),
                                display_order=col_def.get("display_order", 0),
                            )

            logger.debug(
                f"🎉 Finished initializing schema(s) for portfolio={self.portfolio.id}")
            return self.schema

        except Exception as e:
            logger.exception(
                f"🔥 Schema initialization failed for portfolio={self.portfolio.id}: {e}")
            raise

    # -------------------------------
    # Column creation
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
            constraints=normalize_constraints(constraints or {}),
            display_order=display_order,
        )

    def add_custom_column(self, title: str, data_type: str, **kwargs):
        return self.add_column(title, data_type, "custom", **kwargs)

    def add_calculated_column(self, title: str, formula_obj, **kwargs):
        return self.add_column(
            title, "decimal", "calculated", formula_obj=formula_obj, **kwargs
        )
