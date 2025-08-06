from rest_framework import serializers
from schemas.models import (
    Schema,
    SchemaColumn,
)


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
            "decimal_places",
        ]
        read_only_fields = ["id", "data_type", "source", "source_field", "is_deletable"]



class SchemaDetailSerializer(serializers.ModelSerializer):
    columns = SchemaColumnSerializer(many=True, read_only=True)

    class Meta:
        model = Schema
        fields = ["id", "name", "schema_type", "created_at", "columns"]

    def get_columns(self, obj):
        """
        Sort and serialize schema columns.
        You could use another sort like `created_at` or add an `order` field in the future.
        """
        columns = obj.columns.order_by("display_order", "id")
        return SchemaColumnSerializer(columns, many=True).data


class SchemaColumnReorderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    display_order = serializers.IntegerField()


class AddFromConfigSerializer(serializers.Serializer):
    source = serializers.ChoiceField(choices=["asset", "holding", "calculated"])
    source_field = serializers.CharField