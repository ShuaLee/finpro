from django.contrib import admin
from portfolios.models import MetalPortfolio
from accounts.config.account_model_registry import get_account_model_map
from schemas.services.schema_initialization import initialize_asset_schema
from portfolios.services.sub_portfolio_deletion import delete_subportfolio_with_schema


@admin.register(MetalPortfolio)
class MetalPortfolioAdmin(admin.ModelAdmin):
    list_display = ("id", "get_user_email", "created_at")
    search_fields = ["portfolio__profile__user__email"]
    readonly_fields = ["created_at"]

    actions = ["delete_with_schema"]

    def get_user_email(self, obj):
        return obj.portfolio.profile.user.email
    get_user_email.short_description = "User Email"
    get_user_email.admin_order_field = "portfolio__profile__user__email"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            account_model_map = get_account_model_map("metal")
            initialize_asset_schema(
                subportfolio=obj,
                schema_type="metal",
                account_model_map=account_model_map,
            )

    def delete_model(self, request, obj):
        delete_subportfolio_with_schema(obj)

    @admin.action(description="Delete portfolios and their schemas")
    def delete_with_schema(self, request, queryset):
        for portfolio in queryset:
            delete_subportfolio_with_schema(portfolio)
        self.message_user(request, f"Deleted {queryset.count()} portfolios and their schemas.")