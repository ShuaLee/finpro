from rest_framework import serializers

from apps.assets.models import Asset, AssetType


class AssetSerializer(serializers.ModelSerializer):
    is_public = serializers.BooleanField(read_only=True)
    is_market_tracked = serializers.BooleanField(read_only=True)
    current_price = serializers.DecimalField(max_digits=50, decimal_places=18, read_only=True)
    asset_type_name = serializers.CharField(source="asset_type.name", read_only=True)
    owner_email = serializers.EmailField(source="owner.user.email", read_only=True)
    market_data_status = serializers.CharField(source="market_data.status", read_only=True)
    market_data_provider = serializers.CharField(source="market_data.provider", read_only=True)
    market_data_symbol = serializers.CharField(source="market_data.provider_symbol", read_only=True)

    class Meta:
        model = Asset
        fields = [
            "id",
            "asset_type",
            "asset_type_name",
            "owner",
            "owner_email",
            "name",
            "symbol",
            "description",
            "data",
            "is_active",
            "is_public",
            "is_market_tracked",
            "current_price",
            "market_data_status",
            "market_data_provider",
            "market_data_symbol",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "owner",
            "owner_email",
            "asset_type_name",
            "is_public",
            "is_market_tracked",
            "current_price",
            "market_data_status",
            "market_data_provider",
            "market_data_symbol",
            "created_at",
            "updated_at",
        ]


class AssetPickerSerializer(serializers.ModelSerializer):
    asset_type_name = serializers.CharField(source="asset_type.name", read_only=True)
    is_public = serializers.BooleanField(read_only=True)
    is_market_tracked = serializers.BooleanField(read_only=True)
    current_price = serializers.DecimalField(max_digits=50, decimal_places=18, read_only=True)
    market_data_status = serializers.CharField(source="market_data.status", read_only=True)

    class Meta:
        model = Asset
        fields = [
            "id",
            "name",
            "symbol",
            "asset_type",
            "asset_type_name",
            "is_active",
            "is_public",
            "is_market_tracked",
            "current_price",
            "market_data_status",
        ]
        read_only_fields = fields


class AssetCreateSerializer(serializers.Serializer):
    asset_type = serializers.PrimaryKeyRelatedField(queryset=AssetType.objects.none())
    name = serializers.CharField(max_length=255)
    symbol = serializers.CharField(required=False, allow_blank=True, max_length=50)
    description = serializers.CharField(required=False, allow_blank=True)
    data = serializers.JSONField(required=False)
    is_active = serializers.BooleanField(required=False, default=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["asset_type"].queryset = AssetType.objects.all()

    def validate_name(self, value):
        return value.strip()

    def validate_symbol(self, value):
        return value.strip().upper()


class AssetUpdateSerializer(serializers.Serializer):
    asset_type = serializers.PrimaryKeyRelatedField(queryset=AssetType.objects.none(), required=False)
    name = serializers.CharField(max_length=255, required=False)
    symbol = serializers.CharField(required=False, allow_blank=True, max_length=50)
    description = serializers.CharField(required=False, allow_blank=True)
    data = serializers.JSONField(required=False)
    is_active = serializers.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["asset_type"].queryset = AssetType.objects.all()

    def validate_name(self, value):
        return value.strip()

    def validate_symbol(self, value):
        return value.strip().upper()
