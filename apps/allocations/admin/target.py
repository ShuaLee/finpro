from django.contrib import admin

from allocations.models import AllocationDimension, AllocationTarget


@admin.register(AllocationDimension)
class AllocationDimensionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "label",
        "scenario",
        "source_identifier",
        "denominator_mode",
        "is_active",
    )
    search_fields = ("name", "label", "source_identifier", "scenario__name")
    list_filter = ("denominator_mode", "is_active")


@admin.register(AllocationTarget)
class AllocationTargetAdmin(admin.ModelAdmin):
    list_display = (
        "key",
        "label",
        "dimension",
        "target_percent",
        "target_value",
        "min_percent",
        "max_percent",
        "is_locked",
        "is_active",
    )
    search_fields = ("key", "label", "dimension__name")
    list_filter = ("is_locked", "is_active")
