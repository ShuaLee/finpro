from django.contrib import admin

from allocations.models import AllocationPlan, AllocationScenario


class AllocationScenarioInline(admin.TabularInline):
    model = AllocationScenario
    extra = 0
    fields = ("name", "label", "is_default", "is_active")


@admin.register(AllocationPlan)
class AllocationPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "label",
        "portfolio",
        "base_scope",
        "base_value_identifier",
        "is_active",
        "updated_at",
    )
    search_fields = ("name", "label", "portfolio__name", "portfolio__profile__user__email")
    list_filter = ("base_scope", "is_active")
    inlines = [AllocationScenarioInline]


@admin.register(AllocationScenario)
class AllocationScenarioAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "label",
        "plan",
        "is_default",
        "is_active",
        "updated_at",
    )
    search_fields = ("name", "label", "plan__name")
    list_filter = ("is_default", "is_active")
