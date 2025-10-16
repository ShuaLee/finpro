from django import forms
from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

from assets.models.details.equity_detail import EquityDetail
from assets.services.syncs.equity_sync import EquitySyncService


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
            path("add-equity/", self.admin_site.admin_view(self.add_equity),
                 name="add_equity"),
        ]
        return custom_urls + urls

    def add_equity(self, request):
        from django.shortcuts import render, redirect

        if request.method == "POST":
            form = AddEquityForm(request.POST)
            if form.is_valid():
                ticker = form.cleaned_data["ticker"].upper()
                try:
                    asset = EquitySyncService.create_from_symbol(
                        ticker)  # <-- you’ll add this if not exists
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
