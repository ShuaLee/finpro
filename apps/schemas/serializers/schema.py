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
            "formula",
            "decimal_places"
        ]


class SchemaDetailSerializer(serializers.ModelSerializer):
    columns = SchemaColumnSerializer(many=True, read_only=True)

    class Meta:
        model = Schema
        fields = ["id", "name", "schema_type", "columns"]