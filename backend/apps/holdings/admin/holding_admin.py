from django.contrib import admin

from apps.holdings.models import Holding, HoldingFactValue, HoldingOverride


class HoldingFactValueInline(admin.TabularInline):
    model = HoldingFactValue
    extra = 0
    autocomplete_fields = ("definition",)


class HoldingOverrideInline(admin.TabularInline):
    model = HoldingOverride
    extra = 0


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = (
        "asset",
        "container",
        "quantity",
        "unit_value",
        "unit_cost_basis",
        "current_value",
        "invested_value",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "container__portfolio",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "asset__name",
        "asset__symbol",
        "container__name",
        "container__portfolio__name",
        "container__portfolio__profile__user__email",
        "notes",
    )
    readonly_fields = (
        "current_value",
        "invested_value",
        "created_at",
        "updated_at",
    )
    inlines = (HoldingFactValueInline, HoldingOverrideInline)
    ordering = ("container", "asset")
