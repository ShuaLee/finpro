from django.contrib import admin, messages
from django.db.models import Count
from accounts.models.stocks import StockAccount
from accounts.services.account_mode_switcher import switch_account_mode


@admin.register(StockAccount)
class StockAccountAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "account_mode",
        "broker",
        "tax_status",
        "currency",
        "stock_portfolio",
        "active_schema_name",
        "current_value_profile_fx",
        "managed_fields_preview",
        "created_at",
    )
    list_filter = ("account_mode", "tax_status", "currency", "broker")
    search_fields = ("name", "broker", "strategy")
    # active_schema is a property, not a FK — don't include in autocomplete_fields
    readonly_fields = ("created_at", "last_synced", "active_schema_name", "current_value_profile_fx")
    actions = ("switch_to_self_managed", "switch_to_managed")

    # Show all fields; we’ll toggle read-only managed fields on self-managed accounts
    fields = (
        "stock_portfolio",
        "name",
        "broker",
        "tax_status",
        "account_mode",           # read-only (see get_readonly_fields)
        "currency",
        "active_schema_name",     # read-only display of derived schema
        # managed-only (left in form but read-only when not applicable)
        "strategy",
        "invested_amount",
        "current_value",
        "created_at",
        "last_synced",
    )

    def get_queryset(self, request):
        # prefetch/annotate for performance or UI
        qs = super().get_queryset(request).select_related(
            "stock_portfolio",
            "stock_portfolio__portfolio__profile",
        ).annotate(holdings_count=Count("holdings"))
        return qs

    # --- Derived display fields ---

    @admin.display(description="Active Schema")
    def active_schema_name(self, obj):
        return getattr(obj.active_schema, "name", "—")

    @admin.display(description="Value (Profile FX)")
    def current_value_profile_fx(self, obj):
        try:
            val = obj.get_value_in_profile_currency()
        except AttributeError:
            # Fallback if you didn’t add helper; compute inline
            from external_data.fx import get_fx_rate
            from decimal import Decimal
            base = obj.get_current_value() or 0
            profile_ccy = obj.stock_portfolio.portfolio.profile.currency
            fx = get_fx_rate(obj.currency, profile_ccy)
            val = (Decimal(str(base)) * Decimal(str(fx or 1))).quantize(Decimal("0.01"))
        return val

    @admin.display(description="Managed Fields")
    def managed_fields_preview(self, obj):
        if obj.account_mode == "managed":
            parts = []
            if obj.strategy:
                parts.append(f"Strategy: {obj.strategy}")
            if obj.invested_amount is not None:
                parts.append(f"Invested: {obj.invested_amount}")
            if obj.current_value is not None:
                parts.append(f"Current: {obj.current_value} {obj.currency}")
            return " | ".join(parts) or "—"
        return "—"

    # --- Form behavior ---

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        # Never allow editing mode directly in admin — use actions below to ensure cleanup via service
        if "account_mode" not in ro:
            ro.append("account_mode")
        # If self-managed, make managed-only fields read-only
        if obj and obj.account_mode == "self_managed":
            for f in ("strategy", "invested_amount", "current_value"):
                if f not in ro:
                    ro.append(f)
        return ro

    # --- Actions to switch modes safely via service ---

    @admin.action(description="Switch selected accounts to Self-Managed")
    def switch_to_self_managed(self, request, queryset):
        switched, blocked, failed = 0, 0, 0
        for account in queryset:
            try:
                # Default: not force — raise if analytics data exists
                switch_account_mode(account, "self_managed", force=False)
                switched += 1
            except Exception as e:
                # You can inspect e to differentiate blocked vs failed if needed
                blocked += 1
        if switched:
            self.message_user(request, f"Switched {switched} account(s) to Self-Managed.", level=messages.SUCCESS)
        if blocked:
            self.message_user(
                request,
                f"{blocked} account(s) could not be switched (clear managed analytics or use force in code).",
                level=messages.WARNING
            )

    @admin.action(description="Switch selected accounts to Managed")
    def switch_to_managed(self, request, queryset):
        switched, blocked, failed = 0, 0, 0
        for account in queryset:
            try:
                # Default: not force — raise if holdings exist
                switch_account_mode(account, "managed", force=False)
                switched += 1
            except Exception as e:
                blocked += 1
        if switched:
            self.message_user(request, f"Switched {switched} account(s) to Managed.", level=messages.SUCCESS)
        if blocked:
            self.message_user(
                request,
                f"{blocked} account(s) could not be switched (delete holdings or use force in code).",
                level=messages.WARNING
            )
