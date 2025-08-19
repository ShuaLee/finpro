from rest_framework import serializers
from schemas.config.utils import get_column_constraints
from schemas.models import SchemaColumnValue
from schemas.services.calculated_column_engine import recalculate_calculated_columns
from schemas.validators import validate_value_against_constraints
from django.core.exceptions import ValidationError as DjangoValidationError


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

        if value not in [None, ""]:
            # Ensure value can be coerced to expected type
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

            # Validate against constraints
            schema_type = column.schema.schema_type if column and column.schema else None
            constraints = get_column_constraints(
                schema_type, column.source, column.source_field) if schema_type else {}

            try:
                validate_value_against_constraints(
                    value, column.data_type, constraints)
            except DjangoValidationError as e:
                raise serializers.ValidationError({"value": e.message})

            # Normalize all-caps strings
            if column.data_type == "string" and constraints.get("all_caps"):
                data["value"] = str(value).upper()

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
