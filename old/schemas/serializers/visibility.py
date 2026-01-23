from rest_framework import serializers
from schemas.models import (
    SchemaColumnVisibility
)


class SchemaColumnVisibilitySerializer(serializers.ModelSerializer):
    column_title = serializers.CharField(source="column.title", read_only=True)

    class Meta:
        model = SchemaColumnVisibility
        fields = ["id", "column", "column_title", "is_visible"]
        read_only_fields = ["id", "column", "column_title"]
