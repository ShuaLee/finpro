from django.contrib import admin

from allocations.models import AllocationEvaluationRun, AllocationGapResult


@admin.register(AllocationEvaluationRun)
class AllocationEvaluationRunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "scenario",
        "status",
        "as_of",
        "started_at",
        "finished_at",
        "created_at",
    )
    search_fields = ("scenario__name",)
    list_filter = ("status",)
    readonly_fields = ("created_at",)


@admin.register(AllocationGapResult)
class AllocationGapResultAdmin(admin.ModelAdmin):
    list_display = (
        "run",
        "dimension",
        "bucket_label_snapshot",
        "actual_value",
        "target_value",
        "gap_value",
        "actual_percent",
        "target_percent",
        "gap_percent",
        "holding_count",
    )
    search_fields = ("bucket_label_snapshot", "dimension__name", "run__scenario__name")
    list_filter = ("dimension",)
    readonly_fields = (
        "run",
        "dimension",
        "target",
        "bucket_label_snapshot",
        "actual_value",
        "target_value",
        "gap_value",
        "actual_percent",
        "target_percent",
        "gap_percent",
        "holding_count",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
