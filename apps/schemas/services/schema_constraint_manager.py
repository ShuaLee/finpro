from decimal import Decimal
from django.core.exceptions import ValidationError

from schemas.models.constraints import MasterConstraint, SchemaConstraint
from schemas.config.constraints_template import CONSTRAINT_TEMPLATES

import logging

logger = logging.getLogger(__name__)


class SchemaConstraintManager:
    """
    Creates SchemaConstraint rows for a SchemaColumn based on:

        1. MasterConstraint templates
        2. Optional template-level overrides (from SchemaTemplateColumn.constraints)
        3. Future auto-detected overrides (e.g., crypto precision)

    """

    # ---------------------------------------------------------
    # MAIN ENTRY POINT
    # ---------------------------------------------------------
    @staticmethod
    def create_from_master(column, overrides=None):
        """
        Create SchemaConstraint objects for a SchemaColumn.

        PRECEDENCE:
            1. Template overrides (from SchemaTemplate.config)
            2. Auto-detected overrides (domain intelligence)
            3. MasterConstraint.default_value
        """

        overrides = overrides or {}

        # Auto-detect constraints (crypto precision, future logic)
        autodetected = SchemaConstraintManager._auto_detect_overrides(column)

        # Template overrides take precedence over auto ones
        merged_overrides = {**autodetected, **overrides}

        masters = MasterConstraint.objects.filter(
            applies_to=column.data_type, is_active=True
        )

        print(f"Creating constraints for column '{column.title}' "
              f"(type={column.data_type}) with overrides={merged_overrides}")

        for master in masters:

            # ---------------------------------------------------------
            # Determine if an override exists
            # ---------------------------------------------------------
            if master.name in merged_overrides:
                raw_value = merged_overrides[master.name]
                value = SchemaConstraintManager._validate_override(
                    master, raw_value)
            else:
                value = master.default_value

            # Normalized storage: always string (your model expects CharField)
            if value is not None:
                value = str(value)

            SchemaConstraint.objects.get_or_create(
                column=column,
                name=master.name,
                defaults={
                    "label": master.label,
                    "applies_to": master.applies_to,
                    "value": value,
                    "min_limit": master.min_limit,
                    "max_limit": master.max_limit,
                    "is_editable": master.is_editable,
                },
            )

    # ---------------------------------------------------------
    # VALIDATE OVERRIDE VALUE
    # ---------------------------------------------------------
    @staticmethod
    def _validate_override(master, override_value):
        """
        Validate & convert override_value based on CONSTRAINT_TEMPLATES.
        """

        # Allow explicit None to override defaults
        if override_value is None:
            return None

        constraint_rules = CONSTRAINT_TEMPLATES.get(master.applies_to, [])
        rule_def = next(
            (r for r in constraint_rules if r["name"] == master.name), None)

        # No rule metadata? Treat it as string (safe fallback)
        if not rule_def:
            return override_value

        value_type = rule_def["type"]

        # ----------------------------
        # Integer constraints
        # ----------------------------
        if value_type == "integer":
            try:
                converted = int(override_value)
            except Exception:
                raise ValidationError(
                    f"Constraint '{master.name}' must be an integer; got '{override_value}'."
                )
            return converted

        # ----------------------------
        # Decimal constraints
        # ----------------------------
        if value_type == "decimal":
            try:
                converted = Decimal(str(override_value))
            except Exception:
                raise ValidationError(
                    f"Constraint '{master.name}' must be a decimal; got '{override_value}'."
                )

            # Range checks from master constraints:
            if master.min_limit not in [None, "", "None"]:
                if converted < Decimal(master.min_limit):
                    raise ValidationError(
                        f"{master.label} cannot be below {master.min_limit}"
                    )

            if master.max_limit not in [None, "", "None"]:
                if converted > Decimal(master.max_limit):
                    raise ValidationError(
                        f"{master.label} cannot exceed {master.max_limit}"
                    )

            return converted

        # ----------------------------
        # String / boolean / url / date
        # ----------------------------
        return override_value

    # ---------------------------------------------------------
    # AUTO-DETECT OVERRIDES (Crypto quantity precision)
    # ---------------------------------------------------------
    @staticmethod
    def _auto_detect_overrides(column):
        """
        Intelligent automatic overrides:
            - Crypto quantity precision,
            - Future domain metadata.

        Returns dict of auto-detected overrides.
        """

        overrides = {}

        # Only applies to crypto_wallet schemas
        if column.schema.account_type != "crypto_wallet":
            return overrides

        # Only decimal fields need precision inference
        if column.data_type != "decimal":
            return overrides

        # Resolve one asset in the portfolio to infer precision
        asset = SchemaConstraintManager._resolve_asset_from_column(column)
        if not asset:
            return overrides

        precision = SchemaConstraintManager._infer_crypto_precision(asset)
        if precision is not None:
            overrides["decimal_places"] = precision

        return overrides

    # ---------------------------------------------------------
    @staticmethod
    def _resolve_asset_from_column(column):
        """
        Resolve the first asset held anywhere in this portfolio.
        This avoids relying on a nonexistent portfolio.holdings relation.
        """

        portfolio = column.schema.portfolio

        # Get all accounts and prefetch holdings + asset
        accounts = portfolio.accounts.prefetch_related(
            "holdings__asset", "holdings"
        )

        for account in accounts:
            for holding in account.holdings.all():
                if holding.asset:
                    return holding.asset

        return None

    # ---------------------------------------------------------
    @staticmethod
    def _infer_crypto_precision(asset):
        """
        Infer decimal precision for crypto based on market_data.
        """
        mdc = getattr(asset, "market_data", None)
        if mdc and mdc.last_price:
            s = str(mdc.last_price)
            if "." in s:
                return len(s.split(".")[1])

        # Fallback common precision
        return 8
