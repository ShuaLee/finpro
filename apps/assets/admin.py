# assets/admin.py
from django.contrib import admin, messages
from django import forms
from django.utils.translation import gettext_lazy as _

from assets.models.assets import Asset, AssetIdentifier
from assets.models.details.equity_detail import EquityDetail
from core.types import DomainType
from assets.services.syncs.asset_sync import AssetSyncService
from assets.services.syncs.equity_sync import EquitySyncService


# -------------------------------------------------------------------
# Asset Viewer Admin (read-only)
# -------------------------------------------------------------------
class AssetIdentifierInline(admin.TabularInline):
    model = AssetIdentifier
    extra = 0
    can_delete = False
    readonly_fields = ("id_type", "value", "is_primary")


class EquityDetailInline(admin.StackedInline):
    model = EquityDetail
    extra = 0
    can_delete = False
    max_num = 1
    readonly_fields = [f.name for f in EquityDetail._meta.fields if f.name not in ("id", "asset")]


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """Read-only asset viewer. Assets cannot be added/edited directly."""
    list_display = ("get_primary_identifier", "name", "asset_type", "created_at")
    list_filter = ("asset_type",)
    search_fields = ("name", "identifiers__value")

    inlines = [AssetIdentifierInline, EquityDetailInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_primary_identifier(self, obj):
        primary_id = obj.identifiers.filter(is_primary=True).first()
        return primary_id.value if primary_id else "-"
    get_primary_identifier.short_description = "Identifier"

    # --- Sync actions ---
    actions = ["sync_profile", "sync_quote"]

    def sync_profile(self, request, queryset):
        success, fail = 0, 0
        for asset in queryset:
            if AssetSyncService.sync(asset, profile=True):
                success += 1
            else:
                fail += 1
        self.message_user(
            request,
            f"Profile sync completed: {success} succeeded, {fail} failed.",
            messages.SUCCESS if fail == 0 else messages.WARNING,
        )
    sync_profile.short_description = "Sync profile from FMP"

    def sync_quote(self, request, queryset):
        success, fail = 0, 0
        for asset in queryset:
            if AssetSyncService.sync(asset, profile=False):
                success += 1
            else:
                fail += 1
        self.message_user(
            request,
            f"Quote sync completed: {success} succeeded, {fail} failed.",
            messages.SUCCESS if fail == 0 else messages.WARNING,
        )
    sync_quote.short_description = "Sync quote from FMP"


# -------------------------------------------------------------------
# Equity Creator Admin (identifier-first)
# -------------------------------------------------------------------
class AddEquityForm(forms.Form):
    ticker = forms.CharField(
        label=_("Ticker Symbol"),
        max_length=20,
        help_text=_("Enter the equity ticker (e.g., AAPL, MSFT)")
    )


@admin.register(EquityDetail)
class EquityCreatorAdmin(admin.ModelAdmin):
    """Entry point for adding equities by ticker."""
    list_display = ("asset", "exchange", "listing_status", "last_updated")
    search_fields = ("asset__name", "asset__identifiers__value", "exchange")

    change_list_template = "admin/add_equity_changelist.html"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path("add-equity/", self.admin_site.admin_view(self.add_equity), name="add_equity"),
        ]
        return custom_urls + urls

    def add_equity(self, request):
        from django.shortcuts import render, redirect

        if request.method == "POST":
            form = AddEquityForm(request.POST)
            if form.is_valid():
                ticker = form.cleaned_data["ticker"].upper()
                try:
                    asset = EquitySyncService.create_from_symbol(ticker)  # <-- you’ll add this if not exists
                    self.message_user(
                        request,
                        f"Equity {ticker} added successfully.",
                        messages.SUCCESS,
                    )
                    return redirect("admin:assets_asset_change", asset.id)
                except Exception as e:
                    self.message_user(
                        request,
                        f"Failed to add equity {ticker}: {e}",
                        messages.ERROR,
                    )
        else:
            form = AddEquityForm()

        return render(
            request,
            "admin/add_equity.html",
            {"form": form, "title": "Add Equity by Ticker"},
        )
