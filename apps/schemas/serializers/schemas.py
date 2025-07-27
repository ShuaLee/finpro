from rest_framework import serializers
from schemas.models.core import Schema, SchemaColumn, SchemaColumnValue


class SchemaColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemaColumn
        fields = ['id', 'title', 'data_type', 'source',
                  'source_field', 'editable', 'is_deletable', 'formula']


class SchemaDetailSerializer(serializers.ModelSerializer):
    columns = SchemaColumnSerializer(many=True, read_only=True)

    class Meta:
        model = Schema
        fields = ['id', 'name', 'schema_type', 'columns']


class AddCustomColumnSerializer(serializers.Serializer):
    title = serializers.CharField()
    data_type = serializers.ChoiceField(
        choices=['decimal', 'integer', 'string', 'date', 'url'])


class AddCalculatedColumnSerializer(serializers.Serializer):
    title = serializers.CharField()
    formula = serializers.CharField()


class SchemaColumnValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemaColumnValue
        fields = ['id', 'value', 'is_edited']
        read_only_fields = ['is_edited']
