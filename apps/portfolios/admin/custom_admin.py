from django.contrib import admin
from portfolios.models import CustomPortfolio

@admin.register(CustomPortfolio)
class CustomPortfolioAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "get_user_email", "created_at")
    search_fields = ["portfolio__profile__user__email", "name", "slug"]
    readonly_fields = ["created_at", "slug"]
    list_filter = ["created_at"]

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