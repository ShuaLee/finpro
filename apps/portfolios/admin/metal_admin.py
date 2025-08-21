from django.contrib import admin
from portfolios.models import MetalPortfolio
from accounts.config.account_model_registry import get_account_model_map
from schemas.services.schema_initialization import initialize_asset_schema


@admin.register(MetalPortfolio)
class MetalPortfolioAdmin(admin.ModelAdmin):
    list_display = ("id", "get_user_email", "created_at")
    search_fields = ["portfolio__profile__user__email"]
    readonly_fields = ["created_at"]

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
