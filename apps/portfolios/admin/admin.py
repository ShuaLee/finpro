from django.contrib import admin
from portfolios.models.portfolio import Portfolio


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "name", "kind", "client_name", "is_main", "created_at")
    list_filter = ("kind", "is_main", "created_at")
    search_fields = (
        "name",
        "profile__user__email",
        "client_name",
    )
    ordering = ("-created_at",)

    fieldsets = (
        (None, {
            "fields": ("profile", "name", "kind", "client_name", "is_main")
        }),
        ("Timestamps", {
            "fields": ("created_at",),
        }),
    )
    readonly_fields = ("created_at",)
