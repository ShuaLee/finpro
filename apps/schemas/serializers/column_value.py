from rest_framework import serializers
from schemas.models import (
    SchemaColumnValue,
)
from schemas.services.calculated_column_engine import recalculate_calculated_columns


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
            raise serializers.ValidationError("Calculated columns cannot be edited.")

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