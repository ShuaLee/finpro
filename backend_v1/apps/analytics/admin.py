from django.contrib import admin

from analytics.models import (
    Analytic,
    AnalyticDimension,
    AnalyticResult,
    AnalyticRun,
    AssetDimensionExposure,
    DimensionBucket,
    HoldingDimensionExposureOverride,
)


@admin.register(Analytic)
class AnalyticAdmin(admin.ModelAdmin):
    list_display = ("id", "portfolio", "name", "value_identifier", "is_active", "is_system")
    list_filter = ("is_active", "is_system")
    search_fields = ("name", "label", "portfolio__name", "portfolio__profile__user__email")


@admin.register(AnalyticDimension)
class AnalyticDimensionAdmin(admin.ModelAdmin):
    list_display = ("id", "analytic", "name", "dimension_type", "source_type", "is_active", "display_order")
    list_filter = ("dimension_type", "source_type", "is_active")
    search_fields = ("name", "label", "analytic__name")


@admin.register(DimensionBucket)
class DimensionBucketAdmin(admin.ModelAdmin):
    list_display = ("id", "dimension", "key", "label", "parent", "is_unknown_bucket", "is_active")
    list_filter = ("is_unknown_bucket", "is_active")
    search_fields = ("key", "label", "dimension__name")


@admin.register(AssetDimensionExposure)
class AssetDimensionExposureAdmin(admin.ModelAdmin):
    list_display = ("id", "dimension", "asset", "bucket", "weight", "source")
    list_filter = ("source",)


@admin.register(HoldingDimensionExposureOverride)
class HoldingDimensionExposureOverrideAdmin(admin.ModelAdmin):
    list_display = ("id", "dimension", "holding", "bucket", "weight")


@admin.register(AnalyticRun)
class AnalyticRunAdmin(admin.ModelAdmin):
    list_display = ("id", "analytic", "status", "triggered_by", "created_at", "finished_at")
    list_filter = ("status",)


@admin.register(AnalyticResult)
class AnalyticResultAdmin(admin.ModelAdmin):
    list_display = ("id", "run", "dimension", "bucket_label_snapshot", "total_value", "percentage", "holding_count")
    list_filter = ("dimension",)
