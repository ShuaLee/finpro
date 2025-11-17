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
        2. Template-level overrides (SchemaTemplateColumn.constraints)
        3. Per-asset intelligence (CryptoDetail.precision)
    """

    # ==========================================================================
    # MAIN ENTRY POINT
    # ==========================================================================
    @staticmethod
    def create_from_master(column, overrides=None):
        """
        Create SchemaConstraint objects for a SchemaColumn.

        Precedence:
            1. Template overrides (from column template)
            2. Per-asset auto overrides (CryptoDetail.precision)
            3. MasterConstraint.default_value
        """
        overrides = overrides or {}

        # Add auto-detected overrides (clean, deterministic)
        autodetected = SchemaConstraintManager._auto_detect_overrides(column)

        # Template overrides override auto-detected ones
        merged_overrides = {**autodetected, **overrides}

        masters = MasterConstraint.objects.filter(
            applies_to=column.data_type,
            is_active=True
        )

        print(
            f"Creating constraints for column '{column.title}' "
            f"(type={column.data_type}) with overrides={merged_overrides}"
        )

        for master in masters:

            if master.name in merged_overrides:
                raw_val = merged_overrides[master.name]
                value = SchemaConstraintManager._validate_override(
                    master, raw_val)
            else:
                value = master.default_value

            # Always saved as string (SchemaConstraint model uses CharField)
            value = str(value) if value is not None else None

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

    # ==========================================================================
    # VALIDATE OVERRIDE VALUE
    # ==========================================================================
    @staticmethod
    def _validate_override(master, override_value):
        """Convert override_value to correct type and validate via constraint metadata."""

        if override_value is None:
            return None

        rule_def = None
        for r in CONSTRAINT_TEMPLATES.get(master.applies_to, []):
            if r["name"] == master.name:
                rule_def = r
                break

        # No rules → string fallback
        if not rule_def:
            return override_value

        value_type = rule_def["type"]

        # ----- INTEGER -----
        if value_type == "integer":
            try:
                return int(override_value)
            except Exception:
                raise ValidationError(
                    f"Constraint '{master.name}' must be an integer; got '{override_value}'."
                )

        # ----- DECIMAL -----
        if value_type == "decimal":
            try:
                dec = Decimal(str(override_value))
            except Exception:
                raise ValidationError(
                    f"Constraint '{master.name}' must be a decimal; got '{override_value}'."
                )

            # Validate within master limits
            if master.min_limit not in [None, "", "None"]:
                if dec < Decimal(master.min_limit):
                    raise ValidationError(
                        f"{master.label} cannot be below {master.min_limit}"
                    )

            if master.max_limit not in [None, "", "None"]:
                if dec > Decimal(master.max_limit):
                    raise ValidationError(
                        f"{master.label} cannot exceed {master.max_limit}"
                    )

            return dec

        # ----- STRING / BOOL / URL / DATE -----
        return override_value

    # ==========================================================================
    # AUTO-DETECTION: Per-Asset Precision (CryptoDetail)
    # ==========================================================================
    @staticmethod
    def _auto_detect_overrides(column):
        """
        Currently only auto-detects crypto decimal precision from CryptoDetail.
        No inference from market_data. No guessing from holdings.
        Clean and deterministic.
        """
        overrides = {}

        # Only decimals can have precision
        if column.data_type != "decimal":
            return overrides

        schema = column.schema
        account = getattr(schema, "account", None)

        if not account:
            return overrides

        # Only crypto wallets get per-asset precision
        if account.account_type != "crypto_wallet":
            return overrides

        # Try to get any asset in this wallet → but more accurately:
        # precision should come from the template (SchemaGenerator)
        # NOT here. So we DO NOT guess from holdings here.
        # This manager only applies when explicitly called during creation.

        # If the schema is generated for a specific asset, we pass asset along
        asset = getattr(column, "_asset_context", None)

        if asset and getattr(asset, "crypto_detail", None):
            precision = asset.crypto_detail.precision
            overrides["decimal_places"] = precision

        return overrides

    # ==========================================================================
    # BUSINESS RULE VALIDATION (min/max ONLY)
    # ==========================================================================
    @staticmethod
    def validate_business_rules_only(account, holding, cleaned_data):
        """
        Used by HoldingForm to apply min_value/max_value validation.
        (No rounding. No decimal_places enforcement.)
        """
        schema = account.active_schema
        if not schema:
            return cleaned_data

        for col in schema.columns.filter(source="holding"):
            field = col.source_field
            value = cleaned_data.get(field)

            if value is None:
                continue

            for c in col.constraints_set.all():

                if c.value in [None, "", "-", "None"]:
                    continue

                # ---- MIN VALUE ----
                if c.name == "min_value":
                    min_val = Decimal(str(c.value))
                    if Decimal(str(value)) < min_val:
                        raise ValidationError(
                            {field: f"{col.title}: value {value} is below minimum {min_val}"}
                        )

                # ---- MAX VALUE ----
                if c.name == "max_value":
                    max_val = Decimal(str(c.value))
                    if Decimal(str(value)) > max_val:
                        raise ValidationError(
                            {field: f"{col.title}: value {value} exceeds maximum {max_val}"}
                        )

        return cleaned_data
