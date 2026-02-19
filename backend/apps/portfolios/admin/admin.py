from django.contrib import admin
from portfolios.models import Portfolio, PortfolioDenomination, PortfolioValuationSnapshot


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "name", "kind", "client_name", "created_at")
    list_filter = ("kind", "created_at")
    search_fields = (
        "name",
        "profile__user__email",
        "client_name",
    )
    ordering = ("-created_at",)

    fieldsets = (
        (None, {
            "fields": ("profile", "name", "kind", "client_name")
        }),
        ("Timestamps", {
            "fields": ("created_at",),
        }),
    )
    readonly_fields = ("created_at",)


@admin.register(PortfolioDenomination)
class PortfolioDenominationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "portfolio",
        "key",
        "kind",
        "reference_code",
        "is_active",
        "is_system",
        "display_order",
    )
    list_filter = ("kind", "is_active", "is_system")
    search_fields = ("portfolio__name", "key", "label", "reference_code")


@admin.register(PortfolioValuationSnapshot)
class PortfolioValuationSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "portfolio",
        "base_value_identifier",
        "profile_currency_code",
        "total_value",
        "captured_at",
    )
    search_fields = ("portfolio__name", "portfolio__profile__user__email")
    list_filter = ("profile_currency_code", "base_value_identifier")
    readonly_fields = ("captured_at",)
