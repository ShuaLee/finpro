from rest_framework import serializers

from assets.models import AssetType, CustomAsset, RealEstateAsset, RealEstateType


class AssetTypeSerializer(serializers.ModelSerializer):
    is_system = serializers.SerializerMethodField()

    class Meta:
        model = AssetType
        fields = ("id", "name", "slug", "is_system")

    def get_is_system(self, obj):
        return obj.created_by_id is None


class AssetTypeCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)


class AssetTypeUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)


class CustomAssetSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="asset_id", read_only=True)
    asset_type_slug = serializers.CharField(source="asset.asset_type.slug", read_only=True)
    currency_code = serializers.CharField(source="currency.code", read_only=True)

    class Meta:
        model = CustomAsset
        fields = (
            "id",
            "name",
            "asset_type_slug",
            "currency_code",
            "reason",
            "requires_review",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "asset_type_slug",
            "reason",
            "created_at",
            "updated_at",
        )


class CustomAssetCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    asset_type_slug = serializers.SlugField()
    currency_code = serializers.CharField(max_length=3)
    requires_review = serializers.BooleanField(default=False)


class CustomAssetUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    currency_code = serializers.CharField(max_length=3, required=False)
    requires_review = serializers.BooleanField(required=False)


class RealEstateTypeSerializer(serializers.ModelSerializer):
    is_system = serializers.SerializerMethodField()

    class Meta:
        model = RealEstateType
        fields = ("id", "name", "description", "is_system")

    def get_is_system(self, obj):
        return obj.created_by_id is None


class RealEstateTypeCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)


class RealEstateTypeUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    description = serializers.CharField(required=False, allow_blank=True)


class RealEstateAssetSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="asset_id", read_only=True)
    property_type = serializers.CharField(source="property_type.name", read_only=True)
    property_type_id = serializers.IntegerField(source="property_type_id", read_only=True)
    country_code = serializers.CharField(source="country.code", read_only=True)
    currency_code = serializers.CharField(source="currency.code", read_only=True)

    class Meta:
        model = RealEstateAsset
        fields = (
            "id",
            "property_type",
            "property_type_id",
            "is_owner_occupied",
            "country_code",
            "city",
            "address",
            "currency_code",
            "notes",
        )
        read_only_fields = ("id", "property_type", "property_type_id", "country_code", "currency_code")


class RealEstateAssetCreateSerializer(serializers.Serializer):
    property_type_id = serializers.IntegerField()
    country_code = serializers.CharField(max_length=2)
    currency_code = serializers.CharField(max_length=3)
    city = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    is_owner_occupied = serializers.BooleanField(default=False)


class RealEstateAssetUpdateSerializer(serializers.Serializer):
    property_type_id = serializers.IntegerField(required=False)
    country_code = serializers.CharField(max_length=2, required=False)
    currency_code = serializers.CharField(max_length=3, required=False)
    city = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    is_owner_occupied = serializers.BooleanField(required=False)
