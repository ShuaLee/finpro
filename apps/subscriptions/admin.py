from django.contrib import admin
from subscriptions.models import Plan, AccountType


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "price_per_month", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug"]
    readonly_fields = ["slug"]
    ordering = ["price_per_month"]


@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name", "slug"]
    readonly_fields = ["slug"]
    ordering = ["name"]
