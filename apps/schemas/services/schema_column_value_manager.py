from schemas.models import SchemaColumnValue
from schemas.validators import validate_constraints
from decimal import Decimal


class SchemaColumnValueManager:
    def __init__(self, scv: SchemaColumnValue):
        self.scv = scv
        self.column = scv.column
        self.holding = scv.holding

    def save_value(self, raw_value, is_edited: bool):
        """
        Save or update the SCV with validation.
        """
        if self.column.source == "holding":
            casted = self._cast_value(raw_value)
            validate_constraints(self.column.data_type,
                                 self.column.constraints)

            setattr(self.holding, self.column.source_field, casted)
            self.holding.save(update_fields=[self.column.source_field])

            self.scv.value = str(casted)
            self.scv.is_edited = False
            return self.scv

        self.scv.is_edited = is_edited
        if is_edited:
            casted = self._cast_value(raw_value)
            validate_constraints(self.column.data_type,
                                 self.column.constraints)
            self.scv.value = str(casted)
        else:
            self.reset_to_source()

        return self.scv

    def reset_to_source(self):
        self.scv.is_edited = False
        self.scv.value = self.resolve()
        return self.scv

    def resolve(self):
        if self.column.formula:
            # Placeholder for future formula logic
            # return self.column.formula.evaluate(self.holding)
            pass

        if self.column.source_field:
            if hasattr(self.holding, self.column.source_field):
                return getattr(self.holding, self.column.source_field, None)

            if hasattr(self.holding, "asset"):
                asset = self.holding.asset
                if asset and hasattr(asset, self.column.source_field):
                    return getattr(asset, self.column.source_field, None)

        return self._static_default(self.column)

    def _cast_value(self, raw_value):
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

    @staticmethod
    def default_for_column(column, holding):
        value = None

        if column.source == "holding" and column.source_field:
            value = getattr(holding, column.source_field, None)

        elif column.source == "asset" and column.source_field:
            asset = getattr(holding, "asset", None)
            if asset:
                value = getattr(asset, column.source_field, None)

        if value is None:
            value = SchemaColumnValueManager._static_default(column)

        return value

    @staticmethod
    def _static_default(column):
        if column.data_type == "decimal":
            dp = int(column.constraints.get("decimal_places", 2))
            return str(Decimal("0").quantize(Decimal(f"1.{'0'*dp}")))
        elif column.data_type == "string":
            return "-"
        elif column.data_type == "integer":
            return "0"
        return None

    @classmethod
    def get_or_create(cls, holding, column):
        scv, created = SchemaColumnValue.objects.get_or_create(
            column=column,
            holding=holding,
            defaults={
                "value": cls.default_for_column(column, holding),
                "is_edited": False,
            },
        )
        return cls(scv)

    def apply_rules(self):
        if self.column.source == "holding":
            self.save_value(self.scv.value, is_edited=False)
        elif self.scv.is_edited:
            self.save_value(self.scv.value, is_edited=True)
        else:
            self.reset_to_source()
