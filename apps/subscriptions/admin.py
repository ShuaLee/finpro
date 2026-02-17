from django.contrib import admin
from subscriptions.models import AccountType, Plan, Subscription
from subscriptions.services import SubscriptionService


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "tier", "price_per_month", "is_active", "client_mode_enabled"]
    list_filter = ["is_active", "tier", "client_mode_enabled"]
    search_fields = ["name", "slug", "tier"]
    readonly_fields = ["slug"]
    ordering = ["price_per_month"]


@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name", "slug"]
    readonly_fields = ["slug"]
    ordering = ["name"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "profile",
        "plan",
        "status",
        "cancel_at_period_end",
        "current_period_start",
        "current_period_end",
    ]
    list_filter = ["status", "cancel_at_period_end", "plan__tier"]
    search_fields = ["profile__user__email", "plan__slug"]
    ordering = ["-created_at"]
    actions = ["set_to_free", "set_to_pro", "set_to_wealth_manager"]

    def _apply_plan_slug(self, queryset, slug):
        plan = Plan.objects.filter(slug=slug, is_active=True).first()
        if not plan:
            return 0

        updated = 0
        for subscription in queryset.select_related("profile"):
            try:
                SubscriptionService.change_plan(profile=subscription.profile, plan=plan)
                updated += 1
            except Exception:
                continue
        return updated

    @admin.action(description="Set selected subscriptions to Free")
    def set_to_free(self, request, queryset):
        updated = self._apply_plan_slug(queryset, "free")
        self.message_user(request, f"Moved {updated} subscription(s) to Free.")

    @admin.action(description="Set selected subscriptions to Pro")
    def set_to_pro(self, request, queryset):
        updated = self._apply_plan_slug(queryset, "pro")
        self.message_user(request, f"Moved {updated} subscription(s) to Pro.")

    @admin.action(description="Set selected subscriptions to Wealth Manager")
    def set_to_wealth_manager(self, request, queryset):
        updated = self._apply_plan_slug(queryset, "wealth-manager")
        self.message_user(request, f"Moved {updated} subscription(s) to Wealth Manager.")
