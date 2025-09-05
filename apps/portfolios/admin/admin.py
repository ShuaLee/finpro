from django.contrib import admin, messages
from django.utils.text import slugify
from portfolios.models.portfolio import Portfolio
from portfolios.models.subportfolio import SubPortfolio
from portfolios.services.subportfolio_manager import SubPortfolioManager


@admin.register(SubPortfolio)
class SubPortfolioAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "name", "slug",
                    "get_user_email", "created_at")
    search_fields = ["portfolio__profile__user__email", "name", "slug", "type"]
    readonly_fields = ["created_at"]
    list_filter = ["type", "created_at"]

    # -------------------------------
    # Helpers
    # -------------------------------
    def get_user_email(self, obj):
        return obj.portfolio.profile.user.email
    get_user_email.short_description = "User Email"
    get_user_email.admin_order_field = "portfolio__profile__user__email"

    # -------------------------------
    # Save logic (slug for custom)
    # -------------------------------
    def save_model(self, request, obj, form, change):
        if obj.type == "custom" and not obj.slug:
            obj.slug = slugify(obj.name or "")
        obj.full_clean()
        super().save_model(request, obj, form, change)

    # -------------------------------
    # Delete logic: remove portfolio + schema
    # -------------------------------
    def delete_model(self, request, obj):
        SubPortfolioManager.delete_subportfolio(obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        # Prevent accidental bulk delete bypassing schema cleanup
        if "delete_selected" in actions:
            del actions["delete_selected"]

        actions["delete_with_schema"] = (
            self.delete_with_schema,
            "delete_with_schema",
            "Delete selected subportfolios and their schemas",
        )
        return actions

    @staticmethod
    def delete_with_schema(modeladmin, request, queryset):
        count = 0
        for sp in queryset:
            SubPortfolioManager.delete_subportfolio(sp)
            count += 1
        modeladmin.message_user(
            request,
            f"✅ Deleted {count} subportfolio(s) and their schemas.",
            level=messages.SUCCESS,
        )


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ["id", "get_email", "created_at"]
    search_fields = ["profile__user__email"]
    list_filter = ["created_at"]

    def get_email(self, obj):
        return obj.profile.user.email
    get_email.short_description = "User Email"
    get_email.admin_order_field = "profile__user__email"

    # Inline subportfolios (unified)
    inlines = []

    class SubPortfolioInline(admin.StackedInline):
        model = SubPortfolio
        extra = 0
        can_delete = False
        readonly_fields = ["created_at"]
        verbose_name_plural = "SubPortfolios"

    inlines = [SubPortfolioInline]
