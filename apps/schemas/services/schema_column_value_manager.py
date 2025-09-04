from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from schemas.models import SchemaColumnValue
from schemas.validators import validate_constraints
from decimal import Decimal


class SchemaColumnValueManager:
    def __init__(self, scv: SchemaColumnValue):
        self.scv = scv
        self.column = scv.column

    # ----------------------------
    # Save / update
    # ----------------------------
    def save_value(self, raw_value, is_edited: bool):
        """
        Save or update the SCV with validation.
        """
        if self.column.source == "holding":
            # Try casting to the right type
            casted = self._cast_value(raw_value)

            # Run constraints (min/max, etc.)
            try:
                validate_constraints(self.column.data_type, self.column.constraints)
            except Exception as e:
                raise ValidationError(f"Invalid value for {self.column.title}: {e}")

            # Update the holding field
            setattr(self.scv.account, self.column.source_field, casted)
            self.scv.account.save(update_fields=[self.column.source_field])

            # Mirror into SCV for consistency
            self.scv.value = str(casted)
            self.scv.is_edited = False
            return self.scv

        # -------------------
        # Non-holding columns
        # -------------------
        self.scv.is_edited = is_edited
        if is_edited:
            casted = self._cast_value(raw_value)
            validate_constraints(self.column.data_type, self.column.constraints)
            self.scv.value = str(casted)
        else:
            self.reset_to_source()

        return self.scv

    def _cast_value(self, raw_value):
        """
        Casts raw value to the SC data type with normalization.
        """
        if raw_value in [None, ""]:
            return None

        dt = self.column.data_type

        if dt == "decimal":
            dp = int(self.column.constraints.get("decimal_places", 2))
            q = Decimal("1." + "0" * dp)
            return Decimal(str(raw_value)).quantize(q)

        if dt == "integer":
            return int(raw_value)

        if dt == "string":
            return str(raw_value)

        return raw_value

    # ----------------------------
    # Reset / source resolution
    # ----------------------------
    def reset_to_source(self):
        """
        Reset SCV back to source-driven value (remove manual edit).
        """
        self.scv.is_edited = False
        self.scv.value = self.resolve()
        return self.scv


    def resolve(self):
        """
        Resolve correct value for this SCV (holding or asset based).
        """
        if self.column.source_field:
            # holding-level first
            if hasattr(self.scv.account, self.column.source_field):
                return getattr(self.scv.account, self.column.source_field, None)

            # fallback: try asset-level (e.g., stock.price)
            if hasattr(self.scv.account, "asset"):
                asset = self.scv.account.asset
                if asset and hasattr(asset, self.column.source_field):
                    return getattr(asset, self.column.source_field, None)

        # fallback default
        return self._static_default(self.column)

    # ----------------------------
    # Default resolution
    # ----------------------------
    @staticmethod
    def default_for_column(column, account):
        """
        Try to resolve a value from holding or asset.
        Fallback to type-safe static default.
        """
        value = None

        # Holding-backed
        if column.source == "holding" and column.source_field:
            value = getattr(account, column.source_field, None)

        # Asset-backed
        elif column.source == "asset" and column.source_field:
            asset = getattr(account, "asset", None)
            if asset:
                value = getattr(asset, column.source_field, None)

        # Fallback
        if value is None:
            value = SchemaColumnValueManager._static_default(column)

        return value

    @staticmethod
    def _static_default(column):
        """
        Static safe defaults by type.
        """
        if column.data_type == "decimal":
            dp = int(column.constraints.get("decimal_places", 2))
            return str(Decimal("0").quantize(Decimal(f"1.{'0'*dp}")))
        elif column.data_type == "string":
            return "-"
        elif column.data_type == "integer":
            return "0"
        return None

    # ----------------------------
    # Creation helpers
    # ----------------------------
    @classmethod
    def get_or_create(cls, account, column):
        """
        Ensure an SCV exists for this account/column.
        """
        ct = ContentType.objects.get_for_model(type(account))
        scv, created = SchemaColumnValue.objects.get_or_create(
            column=column,
            account_ct=ct,
            account_id=account.id,
            defaults={
                "value": cls.default_for_column(column, account),
                "is_edited": False,
            }
        )
        return cls(scv)
    
    def apply_rules(self):
        if self.column.source == "holding":
            self.save_value(self.scv.value, is_edited=False)
        elif self.scv.is_edited:
            self.save_value(self.scv.value, is_edited=True)
        else:
            self.reset_to_source()