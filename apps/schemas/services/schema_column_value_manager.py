from django.contrib.contenttypes.models import ContentType
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
            # direct edit -> update the holding model
            setattr(self.scv.account, self.column.source_field, raw_value)
            self.scv.account.save(update_fields=[self.column.source_field])
            return self.scv.account

        self.scv.is_edited = is_edited
        if is_edited:
            casted = self._cast_value(raw_value)
            validate_constraints(self.column.data_type,
                                 self.column.constraints)
            self.scv.value = str(casted)  # store as str for TextField
        else:
            self.scv.save()
            return self.scv

    def _cast_value(self, raw_value):
        """
        Casts raw value to the SC data type.
        """
        if raw_value in [None, ""]:
            return None
        dt = self.column.data_type
        if dt == "decimal":
            return Decimal(str(raw_value))
        if dt == "string":
            return str(raw_value)
        return raw_value

    # ----------------------------
    # Reset / source resolution
    # ----------------------------
    def reset_to_source(self):
        """
        Reset SCV back to source-driven value (remove manual edit)
        """
        self.scv.is_edited = False
        self.scv.value = self._resolve_source_value()
        self.scv.save()
        return self.scv

    def _resolve_source_value(self):
        """
        Resolve SCV from column definition if not edited.
        """
        if self.column.source_field:
            return getattr(self.scv.account, self.column.source_field, None)

        # fallback default
        return self._get_default_value()

    def _get_default_value(self):
        """
        Provide a default value based on data type + constraints.
        """
        if self.column.data_type == "decimal":
            dp = int(self.column.constraints.get("decimal_places", 2))
            return str(Decimal("0").quantize(Decimal(f"1.{'0'*dp}")))
        elif self.column.data_type == "string":
            return "-"
        elif self.column.data_type == "integer":
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
                "value": cls._static_default(column),
                "is_edited": False,
            }
        )
        return cls(scv)

    @staticmethod
    def _static_default(column):
        """
        Static default helper for classmethod use.
        """
        if column.data_type == "decimal":
            dp = int(column.constraints.get("decimal_places", 2))
            return str(Decimal("0").quantize(Decimal(f"1.{'0'*dp}")))
        elif column.data_type == "string":
            return "-"
        elif column.data_type == "integer":
            return "0"
        return None
