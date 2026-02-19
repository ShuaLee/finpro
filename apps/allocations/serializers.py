from rest_framework import serializers

from allocations.models import (
    AllocationDimension,
    AllocationEvaluationRun,
    AllocationGapResult,
    AllocationPlan,
    AllocationScenario,
    AllocationTarget,
)


class AllocationPlanSerializer(serializers.ModelSerializer):
    scenario_count = serializers.IntegerField(source="scenarios.count", read_only=True)

    class Meta:
        model = AllocationPlan
        fields = (
            "id",
            "portfolio",
            "name",
            "label",
            "description",
            "base_value_identifier",
            "base_scope",
            "account_type",
            "is_active",
            "scenario_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "scenario_count",
            "created_at",
            "updated_at",
        )


class AllocationPlanCreateSerializer(serializers.Serializer):
    portfolio_id = serializers.IntegerField()
    name = serializers.SlugField(max_length=100)
    label = serializers.CharField(max_length=150)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    base_value_identifier = serializers.SlugField(required=False, default="current_value")
    base_scope = serializers.ChoiceField(choices=AllocationPlan.BaseScope.choices, required=False)
    account_type_id = serializers.IntegerField(required=False, allow_null=True)


class AllocationPlanPatchSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=150, required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    base_value_identifier = serializers.SlugField(required=False)
    base_scope = serializers.ChoiceField(choices=AllocationPlan.BaseScope.choices, required=False)
    account_type_id = serializers.IntegerField(required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False)


class AllocationScenarioSerializer(serializers.ModelSerializer):
    dimension_count = serializers.IntegerField(source="dimensions.count", read_only=True)

    class Meta:
        model = AllocationScenario
        fields = (
            "id",
            "plan",
            "name",
            "label",
            "description",
            "is_default",
            "is_active",
            "dimension_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "plan",
            "dimension_count",
            "created_at",
            "updated_at",
        )


class AllocationScenarioCreateSerializer(serializers.Serializer):
    name = serializers.SlugField(max_length=100)
    label = serializers.CharField(max_length=150)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_default = serializers.BooleanField(required=False, default=False)
    is_active = serializers.BooleanField(required=False, default=True)


class AllocationScenarioPatchSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=150, required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_default = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)


class AllocationDimensionSerializer(serializers.ModelSerializer):
    target_count = serializers.IntegerField(source="targets.count", read_only=True)

    class Meta:
        model = AllocationDimension
        fields = (
            "id",
            "scenario",
            "name",
            "label",
            "description",
            "source_identifier",
            "source_analytic_name",
            "denominator_mode",
            "is_active",
            "display_order",
            "target_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "scenario",
            "target_count",
            "created_at",
            "updated_at",
        )


class AllocationDimensionCreateSerializer(serializers.Serializer):
    name = serializers.SlugField(max_length=100)
    label = serializers.CharField(max_length=150)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    source_identifier = serializers.SlugField(max_length=100)
    source_analytic_name = serializers.SlugField(max_length=100, required=False, allow_null=True, allow_blank=True)
    denominator_mode = serializers.ChoiceField(choices=AllocationDimension.DenominatorMode.choices, required=False)
    is_active = serializers.BooleanField(required=False, default=True)
    display_order = serializers.IntegerField(required=False, min_value=0, default=0)


class AllocationDimensionPatchSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=150, required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    source_identifier = serializers.SlugField(max_length=100, required=False)
    source_analytic_name = serializers.SlugField(max_length=100, required=False, allow_null=True, allow_blank=True)
    denominator_mode = serializers.ChoiceField(choices=AllocationDimension.DenominatorMode.choices, required=False)
    is_active = serializers.BooleanField(required=False)
    display_order = serializers.IntegerField(required=False, min_value=0)


class AllocationTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllocationTarget
        fields = (
            "id",
            "dimension",
            "key",
            "label",
            "target_percent",
            "target_value",
            "min_percent",
            "max_percent",
            "is_locked",
            "priority",
            "display_order",
            "is_active",
        )
        read_only_fields = ("id", "dimension")


class AllocationTargetCreateSerializer(serializers.Serializer):
    key = serializers.SlugField(max_length=100)
    label = serializers.CharField(max_length=150)
    target_percent = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    target_value = serializers.DecimalField(max_digits=20, decimal_places=2, required=False, allow_null=True)
    min_percent = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    max_percent = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    is_locked = serializers.BooleanField(required=False, default=False)
    priority = serializers.IntegerField(required=False, min_value=0, default=0)
    display_order = serializers.IntegerField(required=False, min_value=0, default=0)
    is_active = serializers.BooleanField(required=False, default=True)


class AllocationTargetPatchSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=150, required=False)
    target_percent = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    target_value = serializers.DecimalField(max_digits=20, decimal_places=2, required=False, allow_null=True)
    min_percent = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    max_percent = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    is_locked = serializers.BooleanField(required=False)
    priority = serializers.IntegerField(required=False, min_value=0)
    display_order = serializers.IntegerField(required=False, min_value=0)
    is_active = serializers.BooleanField(required=False)


class AllocationEvaluationRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllocationEvaluationRun
        fields = (
            "id",
            "scenario",
            "status",
            "as_of",
            "started_at",
            "finished_at",
            "error_message",
            "triggered_by",
            "created_at",
        )


class AllocationGapResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllocationGapResult
        fields = (
            "id",
            "run",
            "dimension",
            "target",
            "bucket_key_snapshot",
            "bucket_label_snapshot",
            "actual_value",
            "target_value",
            "gap_value",
            "actual_percent",
            "target_percent",
            "gap_percent",
            "holding_count",
        )
