from rest_framework import serializers
from schemas.config.utils import get_column_constraints
from schemas.models import (
    SchemaColumnValue,
)
from schemas.services.calculated_column_engine import recalculate_calculated_columns
from decimal import Decimal


class SchemaColumnValueSerializer(serializers.ModelSerializer):
    value = serializers.CharField(allow_blank=True, allow_null=True)

    class Meta:
        model = SchemaColumnValue
        fields = ["id", "value", "is_edited"]
        read_only_fields = ["id", "is_edited"]

    def validate(self, data):
        value = data.get("value")
        column = self.instance.column

        if column.source == "calculated":
            raise serializers.ValidationError(
                "Calculated columns cannot be edited.")

        if not column.editable:
            raise serializers.ValidationError("This column is not editable.")

        # Type validation
        if value not in [None, ""]:
            try:
                if column.data_type == "decimal":
                    float(value)
                elif column.data_type == "integer":
                    int(value)
                elif column.data_type == "string":
                    str(value)
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    "value": f"Invalid input for type '{column.data_type}'."
                })

        # Constraints
        schema_type = column.schema.schema_type if column and column.schema else None
        constraints = get_column_constraints(
            schema_type, column.source, column.source_field) if schema_type else {}

        if column.data_type == "decimal" and value not in [None, ""]:
            try:
                dec = Decimal(str(value))
                min_ = constraints.get("min")
                max_ = constraints.get("max")
                if min_ is not None and dec < Decimal(str(min_)):
                    raise serializers.ValidationError(
                        {"value": f"Must be ≥ {min_}."})
                if max_ is not None and dec > Decimal(str(max_)):
                    raise serializers.ValidationError(
                        {"value": f"Must be ≤ {max_}."})
            except Exception:
                pass

        if column.data_type == "string" and value not in [None, ""]:
            s = str(value)
            minimum = constraints.get("character_minimum")
            limit = constraints.get("character_limit")
            if minimum is not None and len(s) < int(minimum):
                raise serializers.ValidationError(
                    {"value": f"Must be at least {minimum} characters."})
            if limit is not None and len(s) > int(limit):
                raise serializers.ValidationError(
                    {"value": f"Must be at most {limit} characters."})
            if constraints.get("all_caps"):
                # normalize the value in validated_data so update() stores uppercase
                data["value"] = s.upper()

        return data

    def update(self, instance, validated_data):
        value = validated_data.get("value")

        if value in [None, ""]:
            instance.value = None
            instance.is_edited = False
        else:
            instance.value = value
            instance.is_edited = True

        instance.save()

        # 🔁 Trigger recalculation of all formulas that depend on this column
        recalculate_calculated_columns(
            instance.column.schema,
            instance.account  # Generic foreign key object
        )

        return instance
