from rest_framework import serializers
from schemas.models import (
    Schema,
    SchemaColumn,
    SchemaColumnValue,
    SchemaColumnVisibility
)
from schemas.services import recalculate_calculated_columns


class SchemaColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemaColumn
        fields = [
            "id",
            "title",
            "data_type",
            "source",
            "source_field",
            "editable",
            "is_deletable",
            "formula",
            "decimal_places"
        ]


class SchemaDetailSerializer(serializers.ModelSerializer):
    columns = SchemaColumnSerializer(many=True, read_only=True)

    class Meta:
        model = Schema
        fields = ["id", "name", "schema_type", "columns"]


class AddCustomColumnSerializer(serializers.Serializer):
    title = serializers.CharField()
    data_type = serializers.ChoiceField(choices=[
        ('decimal', 'Decimal'),
        ('integer', 'Integer'),
        ('string', 'Text'),
        ('date', 'Date'),
        ('url', 'URL'),
    ])


class AddCalculatedColumnSerializer(serializers.Serializer):
    title = serializers.CharField()
    formula = serializers.CharField()


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


class SchemaColumnVisibilitySerializer(serializers.ModelSerializer):
    column_title = serializers.CharField(source="column.title", read_only=True)

    class Meta:
        model = SchemaColumnVisibility
        fields = ["id", "column", "column_title", "is_visible"]
        read_only_fields = ["id", "column", "column_title"]
