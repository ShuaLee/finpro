from django.contrib import admin

from apps.holdings.models import Holding


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
    ordering = ("container", "asset")
