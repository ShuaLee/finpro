from rest_framework import serializers

from apps.holdings.models import Container, Portfolio


class ContainerSerializer(serializers.ModelSerializer):
    portfolio_name = serializers.CharField(source="portfolio.name", read_only=True)

    class Meta:
        model = Container
        fields = [
            "id",
            "portfolio",
            "portfolio_name",
            "name",
            "kind",
            "description",
            "is_tracked",
            "source",
            "external_id",
            "external_parent_id",
            "last_synced_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "portfolio_name",
            "created_at",
            "updated_at",
        ]


class ContainerCreateSerializer(serializers.Serializer):
    portfolio = serializers.PrimaryKeyRelatedField(queryset=Portfolio.objects.all())
    name = serializers.CharField(max_length=100)
    kind = serializers.CharField(required=False, allow_blank=True, max_length=50)
    description = serializers.CharField(required=False, allow_blank=True, max_length=255)
    is_tracked = serializers.BooleanField(required=False, default=False)
    source = serializers.CharField(required=False, allow_blank=True, max_length=50)
    external_id = serializers.CharField(required=False, allow_blank=True, max_length=255)
    external_parent_id = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_name(self, value):
        return value.strip()

    def validate_kind(self, value):
        return value.strip()

    def validate_description(self, value):
        return value.strip()

    def validate_source(self, value):
        return value.strip()

    def validate_external_id(self, value):
        return value.strip()

    def validate_external_parent_id(self, value):
        return value.strip()


class ContainerUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    kind = serializers.CharField(required=False, allow_blank=True, max_length=50)
    description = serializers.CharField(required=False, allow_blank=True, max_length=255)
    is_tracked = serializers.BooleanField(required=False)
    source = serializers.CharField(required=False, allow_blank=True, max_length=50)
    external_id = serializers.CharField(required=False, allow_blank=True, max_length=255)
    external_parent_id = serializers.CharField(required=False, allow_blank=True, max_length=255)
    last_synced_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate_name(self, value):
        return value.strip()

    def validate_kind(self, value):
        return value.strip()

    def validate_description(self, value):
        return value.strip()

    def validate_source(self, value):
        return value.strip()

    def validate_external_id(self, value):
        return value.strip()

    def validate_external_parent_id(self, value):
        return value.strip()
