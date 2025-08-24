from django.contrib import admin, messages
from schemas.services.schema_initialization import initialize_asset_schema
from portfolios.services.sub_portfolio_deletion import delete_subportfolio_with_schema


class BaseSubPortfolioAdmin(admin.ModelAdmin):
    list_display = ("id", "get_user_email", "created_at")
    search_fields = ["portfolio__profile__user__email"]
    readonly_fields = ["created_at"]

    schema_type = None  # Must be overridden
    account_model_key = None  # Must be overridden

    def get_user_email(self, obj):
        return obj.portfolio.profile.user.email
    get_user_email.short_description = "User Email"
    get_user_email.admin_order_field = "portfolio__profile__user__email"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            from accounts.config.account_model_registry import get_account_model_map
            account_model_map = get_account_model_map(self.account_model_key)
            initialize_asset_schema(
                subportfolio=obj,
                schema_type=self.schema_type,
                account_model_map=account_model_map,
            )

    def delete_model(self, request, obj):
        delete_subportfolio_with_schema(obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        actions["delete_with_schema"] = (
            self.delete_with_schema,
            "delete_with_schema",
            "Delete selected portfolios and their schemas"
        )
        return actions

    @staticmethod
    def delete_with_schema(modeladmin, request, queryset):
        count = 0
        for portfolio in queryset:
            delete_subportfolio_with_schema(portfolio)
            count += 1
        modeladmin.message_user(
            request, f"✅ Deleted {count} portfolio(s) and their schemas.", level=messages.SUCCESS
        )
