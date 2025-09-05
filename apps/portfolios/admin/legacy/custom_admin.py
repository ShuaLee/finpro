from django.contrib import admin
from portfolios.models import CustomPortfolio
from portfolios.services.sub_portfolio_deletion import delete_subportfolio_with_schema

@admin.register(CustomPortfolio)
class CustomPortfolioAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "get_user_email", "created_at")
    search_fields = ["portfolio__profile__user__email", "name", "slug"]
    readonly_fields = ["created_at", "slug"]
    list_filter = ["created_at"]

    actions = ["delete_with_schema"]

    def get_user_email(self, obj):
        return obj.portfolio.profile.user.email
    get_user_email.short_description = "User Email"
    get_user_email.admin_order_field = "portfolio__profile__user__email"

    def save_model(self, request, obj, form, change):
        if not obj.slug:
            from django.utils.text import slugify
            obj.slug = slugify(obj.name or "")
        obj.full_clean()
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        delete_subportfolio_with_schema(obj)

    @admin.action(description="Delete portfolios and their schemas")
    def delete_with_schema(self, request, queryset):
        for portfolio in queryset:
            delete_subportfolio_with_schema(portfolio)
        self.message_user(request, f"Deleted {queryset.count()} portfolios and their schemas.")