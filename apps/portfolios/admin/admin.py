from django.contrib import admin
from portfolios.models.portfolio import Portfolio


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "name", "is_main", "created_at")
    list_filter = ("is_main", "created_at")
    search_fields = (
        "name",
        "profile__user__username",
        "profile__user__email",
    )
    ordering = ("-created_at",)

    fieldsets = (
        (None, {
            "fields": ("profile", "name", "is_main")
        }),
        ("Timestamps", {
            "fields": ("created_at",),
        }),
    )
    readonly_fields = ("created_at",)
