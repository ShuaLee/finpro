from rest_framework import serializers

from analytics.models import (
    Analytic,
    AnalyticDimension,
    AnalyticResult,
    AnalyticRun,
    AssetDimensionExposure,
    DimensionBucket,
    HoldingDimensionExposureOverride,
)


class AnalyticSerializer(serializers.ModelSerializer):
    dimension_count = serializers.IntegerField(source="dimensions.count", read_only=True)

    class Meta:
        model = Analytic
        fields = (
            "id",
            "portfolio",
            "name",
            "label",
            "description",
            "value_identifier",
            "is_active",
            "is_system",
            "dimension_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "is_system",
            "dimension_count",
            "created_at",
            "updated_at",
        )


class AnalyticCreateSerializer(serializers.Serializer):
    portfolio_id = serializers.IntegerField()
    name = serializers.SlugField(max_length=100)
    label = serializers.CharField(max_length=150)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    value_identifier = serializers.SlugField(max_length=100, required=False, default="current_value")


class AnalyticPatchSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=150, required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    value_identifier = serializers.SlugField(max_length=100, required=False)
    is_active = serializers.BooleanField(required=False)


class DimensionSerializer(serializers.ModelSerializer):
    bucket_count = serializers.IntegerField(source="buckets.count", read_only=True)

    class Meta:
        model = AnalyticDimension
        fields = (
            "id",
            "analytic",
            "name",
            "label",
            "description",
            "dimension_type",
            "source_type",
            "source_identifier",
            "is_active",
            "display_order",
            "bucket_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "analytic",
            "bucket_count",
            "created_at",
            "updated_at",
        )


class DimensionCreateSerializer(serializers.Serializer):
    name = serializers.SlugField(max_length=100)
    label = serializers.CharField(max_length=150)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    dimension_type = serializers.ChoiceField(choices=AnalyticDimension.DimensionType.choices)
    source_type = serializers.ChoiceField(choices=AnalyticDimension.SourceType.choices)
    source_identifier = serializers.SlugField(max_length=100, required=False, allow_blank=True, allow_null=True)
    display_order = serializers.IntegerField(required=False, min_value=0, default=0)


class DimensionPatchSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=150, required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    source_identifier = serializers.SlugField(max_length=100, required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False)
    display_order = serializers.IntegerField(required=False, min_value=0)


class BucketSerializer(serializers.ModelSerializer):
    class Meta:
        model = DimensionBucket
        fields = (
            "id",
            "dimension",
            "key",
            "label",
            "parent",
            "is_unknown_bucket",
            "is_active",
            "display_order",
        )
        read_only_fields = (
            "id",
            "dimension",
        )


class BucketCreateSerializer(serializers.Serializer):
    key = serializers.SlugField(max_length=100)
    label = serializers.CharField(max_length=150)
    parent_id = serializers.IntegerField(required=False, allow_null=True)
    is_unknown_bucket = serializers.BooleanField(required=False, default=False)
    is_active = serializers.BooleanField(required=False, default=True)
    display_order = serializers.IntegerField(required=False, min_value=0, default=0)


class BucketPatchSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=150, required=False)
    parent_id = serializers.IntegerField(required=False, allow_null=True)
    is_unknown_bucket = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)
    display_order = serializers.IntegerField(required=False, min_value=0)


class AssetExposureSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetDimensionExposure
        fields = (
            "id",
            "dimension",
            "asset",
            "bucket",
            "weight",
            "source",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "dimension",
            "source",
            "created_at",
            "updated_at",
        )


class AssetExposureUpsertItemSerializer(serializers.Serializer):
    asset_id = serializers.UUIDField()
    bucket_id = serializers.IntegerField()
    weight = serializers.DecimalField(max_digits=9, decimal_places=6, min_value=0, max_value=1)


class HoldingOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model = HoldingDimensionExposureOverride
        fields = (
            "id",
            "dimension",
            "holding",
            "bucket",
            "weight",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "dimension",
            "created_at",
            "updated_at",
        )


class HoldingOverrideUpsertItemSerializer(serializers.Serializer):
    holding_id = serializers.IntegerField()
    bucket_id = serializers.IntegerField()
    weight = serializers.DecimalField(max_digits=9, decimal_places=6, min_value=0, max_value=1)


class AnalyticRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticRun
        fields = (
            "id",
            "analytic",
            "status",
            "as_of",
            "started_at",
            "finished_at",
            "error_message",
            "triggered_by",
            "created_at",
        )


class AnalyticResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticResult
        fields = (
            "id",
            "run",
            "dimension",
            "bucket",
            "bucket_label_snapshot",
            "total_value",
            "percentage",
            "holding_count",
        )
