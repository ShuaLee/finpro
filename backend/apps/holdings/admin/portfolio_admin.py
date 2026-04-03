from django.contrib import admin

from apps.holdings.models import Portfolio


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "profile",
        "kind",
        "is_default",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "kind",
        "is_default",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "name",
        "profile__user__email",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    ordering = ("profile", "name")

