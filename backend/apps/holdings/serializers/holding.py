from rest_framework import serializers

from apps.assets.models import Asset, AssetType
from apps.holdings.models import Container, Holding, HoldingFactDefinition, HoldingFactValue, HoldingOverride, Portfolio
from apps.holdings.services.value_utils import parse_typed_value


class HoldingFactDefinitionSerializer(serializers.ModelSerializer):
    portfolio_name = serializers.CharField(source="portfolio.name", read_only=True)

    class Meta:
        model = HoldingFactDefinition
        fields = [
            "id",
            "portfolio",
            "portfolio_name",
            "key",
            "label",
            "description",
            "data_type",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "portfolio_name", "created_at", "updated_at"]


class HoldingFactDefinitionCreateSerializer(serializers.Serializer):
    portfolio = serializers.PrimaryKeyRelatedField(queryset=Portfolio.objects.all())
    key = serializers.SlugField(max_length=100)
    label = serializers.CharField(max_length=150)
    description = serializers.CharField(required=False, allow_blank=True)
    data_type = serializers.ChoiceField(
        choices=[choice[0] for choice in HoldingFactDefinition._meta.get_field("data_type").choices]
    )
    is_active = serializers.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["portfolio"].queryset = Portfolio.objects.all()

    def validate_label(self, value):
        return value.strip()

    def validate_description(self, value):
        return value.strip()


class HoldingFactValueSerializer(serializers.ModelSerializer):
    definition_key = serializers.CharField(source="definition.key", read_only=True)
    definition_label = serializers.CharField(source="definition.label", read_only=True)
    definition_data_type = serializers.CharField(source="definition.data_type", read_only=True)
    typed_value = serializers.SerializerMethodField()

    class Meta:
        model = HoldingFactValue
        fields = [
            "id",
            "holding",
            "definition",
            "definition_key",
            "definition_label",
            "definition_data_type",
            "value",
            "typed_value",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "definition_key", "definition_label", "definition_data_type", "created_at", "updated_at"]

    def get_typed_value(self, obj):
        return parse_typed_value(data_type=obj.definition.data_type, raw_value=obj.value)


class HoldingFactValueUpsertSerializer(serializers.Serializer):
    definition = serializers.PrimaryKeyRelatedField(queryset=HoldingFactDefinition.objects.all())
    value = serializers.JSONField(required=False, allow_null=True)


class HoldingOverrideSerializer(serializers.ModelSerializer):
    typed_value = serializers.SerializerMethodField()

    class Meta:
        model = HoldingOverride
        fields = [
            "id",
            "holding",
            "key",
            "data_type",
            "value",
            "typed_value",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_typed_value(self, obj):
        return parse_typed_value(data_type=obj.data_type, raw_value=obj.value)


class HoldingOverrideUpsertSerializer(serializers.Serializer):
    key = serializers.SlugField(max_length=100)
    data_type = serializers.ChoiceField(
        choices=[choice[0] for choice in HoldingOverride._meta.get_field("data_type").choices]
    )
    value = serializers.JSONField(required=False, allow_null=True)


class HoldingSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source="asset.name", read_only=True)
    asset_symbol = serializers.CharField(source="asset.symbol", read_only=True)
    asset_current_price = serializers.DecimalField(
        source="asset.current_price",
        max_digits=50,
        decimal_places=18,
        read_only=True,
    )
    asset_current_price_as_of = serializers.DateTimeField(
        source="asset.current_price_as_of",
        read_only=True,
    )
    asset_current_price_is_fresh = serializers.BooleanField(
        source="asset.current_price_is_fresh",
        read_only=True,
    )
    effective_price = serializers.DecimalField(max_digits=50, decimal_places=18, read_only=True)
    effective_current_value = serializers.DecimalField(max_digits=50, decimal_places=18, read_only=True)
    effective_sector = serializers.CharField(read_only=True, allow_null=True)
    effective_industry = serializers.CharField(read_only=True, allow_null=True)
    fx_rate = serializers.DecimalField(max_digits=30, decimal_places=10, read_only=True)
    market_value = serializers.DecimalField(max_digits=50, decimal_places=18, read_only=True)
    current_value_profile = serializers.DecimalField(max_digits=50, decimal_places=18, read_only=True)
    cost_basis_profile = serializers.DecimalField(max_digits=50, decimal_places=18, read_only=True)
    unrealized_gain = serializers.DecimalField(max_digits=50, decimal_places=18, read_only=True)
    unrealized_gain_pct = serializers.DecimalField(max_digits=50, decimal_places=18, read_only=True)
    fact_values = HoldingFactValueSerializer(many=True, read_only=True)
    overrides = HoldingOverrideSerializer(many=True, read_only=True)
    container_name = serializers.CharField(source="container.name", read_only=True)
    current_value = serializers.DecimalField(max_digits=50, decimal_places=18, read_only=True)
    invested_value = serializers.DecimalField(max_digits=50, decimal_places=18, read_only=True)

    class Meta:
        model = Holding
        fields = [
            "id",
            "container",
            "container_name",
            "asset",
            "asset_name",
            "asset_symbol",
            "asset_current_price",
            "asset_current_price_as_of",
            "asset_current_price_is_fresh",
            "effective_price",
            "effective_current_value",
            "effective_sector",
            "effective_industry",
            "fx_rate",
            "market_value",
            "current_value_profile",
            "cost_basis_profile",
            "unrealized_gain",
            "unrealized_gain_pct",
            "quantity",
            "unit_value",
            "unit_cost_basis",
            "current_value",
            "invested_value",
            "notes",
            "data",
            "fact_values",
            "overrides",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "container_name",
            "asset_name",
            "asset_symbol",
            "asset_current_price",
            "asset_current_price_as_of",
            "asset_current_price_is_fresh",
            "effective_price",
            "effective_current_value",
            "effective_sector",
            "effective_industry",
            "fx_rate",
            "market_value",
            "current_value_profile",
            "cost_basis_profile",
            "unrealized_gain",
            "unrealized_gain_pct",
            "current_value",
            "invested_value",
            "created_at",
            "updated_at",
        ]




class HoldingCreateSerializer(serializers.Serializer):
    container = serializers.PrimaryKeyRelatedField(queryset=Container.objects.all())
    asset = serializers.PrimaryKeyRelatedField(queryset=Asset.objects.all())
    quantity = serializers.DecimalField(max_digits=40, decimal_places=18, required=False)
    unit_value = serializers.DecimalField(max_digits=40, decimal_places=18, required=False, allow_null=True)
    unit_cost_basis = serializers.DecimalField(max_digits=40, decimal_places=18, required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    data = serializers.JSONField(required=False)

    def validate_notes(self, value):
        return value.strip()


class HoldingUpdateSerializer(serializers.Serializer):
    quantity = serializers.DecimalField(max_digits=40, decimal_places=18, required=False)
    unit_value = serializers.DecimalField(max_digits=40, decimal_places=18, required=False, allow_null=True)
    unit_cost_basis = serializers.DecimalField(max_digits=40, decimal_places=18, required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    data = serializers.JSONField(required=False)

    def validate_notes(self, value):
        return value.strip()


class HoldingCreateWithAssetSerializer(serializers.Serializer):
    container = serializers.PrimaryKeyRelatedField(queryset=Container.objects.all())
    asset = serializers.PrimaryKeyRelatedField(queryset=Asset.objects.all(), required=False, allow_null=True)
    active_equity_symbol = serializers.CharField(required=False, allow_blank=False, max_length=50)
    active_crypto_symbol = serializers.CharField(required=False, allow_blank=False, max_length=50)
    active_commodity_symbol = serializers.CharField(required=False, allow_blank=False, max_length=50)
    precious_metal_code = serializers.CharField(required=False, allow_blank=False, max_length=50)
    quantity = serializers.DecimalField(max_digits=40, decimal_places=18, required=False)
    unit_value = serializers.DecimalField(max_digits=40, decimal_places=18, required=False, allow_null=True)
    unit_cost_basis = serializers.DecimalField(max_digits=40, decimal_places=18, required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    data = serializers.JSONField(required=False)
    asset_name = serializers.CharField(max_length=255, required=False)
    asset_type = serializers.PrimaryKeyRelatedField(queryset=AssetType.objects.none(), required=False)
    asset_symbol = serializers.CharField(required=False, allow_blank=True, max_length=50)
    asset_description = serializers.CharField(required=False, allow_blank=True)
    asset_data = serializers.JSONField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["asset_type"].queryset = AssetType.objects.all()

    def validate_notes(self, value):
        return value.strip()

    def validate_asset_name(self, value):
        return value.strip()

    def validate_asset_symbol(self, value):
        return value.strip().upper()

    def validate_active_equity_symbol(self, value):
        return value.strip().upper()

    def validate_active_crypto_symbol(self, value):
        return value.strip().upper()

    def validate_active_commodity_symbol(self, value):
        return value.strip().upper()

    def validate_precious_metal_code(self, value):
        return value.strip().lower()

    def validate_asset_description(self, value):
        return value.strip()

    def validate(self, attrs):
        asset = attrs.get("asset")
        active_equity_symbol = attrs.get("active_equity_symbol")
        active_crypto_symbol = attrs.get("active_crypto_symbol")
        active_commodity_symbol = attrs.get("active_commodity_symbol")
        precious_metal_code = attrs.get("precious_metal_code")
        asset_name = attrs.get("asset_name")
        asset_type = attrs.get("asset_type")
        tracked_selection_count = sum(
            bool(value)
            for value in (
                active_equity_symbol,
                active_crypto_symbol,
                active_commodity_symbol,
                precious_metal_code,
            )
        )

        if asset is None and tracked_selection_count == 0 and not asset_name:
            raise serializers.ValidationError(
                {
                    "asset": (
                        "Select an existing asset, choose an active market asset, or provide data for a new asset."
                    )
                }
            )

        if asset is not None and (
            tracked_selection_count > 0 or asset_name or asset_type
        ):
            raise serializers.ValidationError(
                "Provide either an existing asset, an active market selection, or new asset details, not both."
            )

        if tracked_selection_count > 1:
            raise serializers.ValidationError(
                "Provide only one active market selection at a time."
            )

        if tracked_selection_count > 0 and (asset_name or asset_type):
            raise serializers.ValidationError(
                "Provide either an active market selection or new asset details, not both."
            )

        if asset is None and tracked_selection_count == 0 and asset_type is None:
            raise serializers.ValidationError(
                {"asset_type": "Asset type is required when creating a new asset."}
            )

        return attrs
