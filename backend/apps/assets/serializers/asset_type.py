from rest_framework import serializers

from apps.assets.models import AssetType


class AssetTypeSerializer(serializers.ModelSerializer):
    is_system = serializers.BooleanField(read_only=True)

    class Meta:
        model = AssetType
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "created_by",
            "is_system",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "created_by",
            "is_system",
            "created_at",
            "updated_at",
        ]


class AssetTypeCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate_name(self, value):
        return value.strip()


class AssetTypeUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate_name(self, value):
        return value.strip()
