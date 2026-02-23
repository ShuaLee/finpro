from rest_framework import serializers

from portfolios.models import DashboardLayoutState, PortfolioDenomination, PortfolioValuationSnapshot


class PortfolioDenominationSerializer(serializers.ModelSerializer):
    currency_code = serializers.CharField(source="currency.code", read_only=True)
    asset_id = serializers.UUIDField(source="asset.id", read_only=True)

    class Meta:
        model = PortfolioDenomination
        fields = (
            "id",
            "portfolio",
            "key",
            "label",
            "kind",
            "currency",
            "currency_code",
            "asset",
            "asset_id",
            "reference_code",
            "unit_label",
            "is_active",
            "is_system",
            "display_order",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "portfolio",
            "is_system",
            "created_at",
            "updated_at",
            "currency_code",
            "asset_id",
        )


class PortfolioDenominationCreateSerializer(serializers.Serializer):
    key = serializers.SlugField(max_length=100)
    label = serializers.CharField(max_length=150)
    kind = serializers.ChoiceField(choices=PortfolioDenomination.Kind.choices)
    currency_code = serializers.CharField(required=False, allow_blank=False)
    asset_id = serializers.UUIDField(required=False)
    reference_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    unit_label = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    display_order = serializers.IntegerField(required=False, min_value=0, default=0)
    is_active = serializers.BooleanField(required=False, default=True)


class PortfolioDenominationPatchSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=150, required=False)
    currency_code = serializers.CharField(required=False, allow_blank=False)
    asset_id = serializers.UUIDField(required=False)
    reference_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    unit_label = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    display_order = serializers.IntegerField(required=False, min_value=0)
    is_active = serializers.BooleanField(required=False)


class PortfolioValuationSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioValuationSnapshot
        fields = (
            "id",
            "portfolio",
            "base_value_identifier",
            "profile_currency_code",
            "total_value",
            "denominations",
            "captured_at",
        )


class DashboardLayoutStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardLayoutState
        fields = (
            "scope",
            "active_layout_id",
            "layouts",
            "updated_at",
        )


class DashboardLayoutStateUpsertSerializer(serializers.Serializer):
    scope = serializers.CharField(max_length=120)
    active_layout_id = serializers.CharField(max_length=100)
    layouts = serializers.ListField(child=serializers.DictField(), allow_empty=True)
