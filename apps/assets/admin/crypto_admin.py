from django import forms
from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

from assets.models.details.crypto_detail import CryptoDetail
from assets.services.syncs.crypto_sync import CryptoSyncService

class AddCryptoForm(forms.Form):
    symbol = forms.CharField(
        label=_("Pair Symbol"),
        max_length=20,
        help_text=_("Enter the crypto pair symbol (e.g., BTCUSD, ETHUSD)")
    )

@admin.register(CryptoDetail)
class CryptoCreatorAdmin(admin.ModelAdmin):
    """Entry point for adding cryptocurrencies by pair symbol."""
    list_display = ("asset", "exchange", "last_updated")
    search_fields = ("asset__name", "asset__identifiers__value", "exchange")

    change_list_template = "admin/add_crypto_changelist.html"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                "add-crypto/",
                self.admin_site.admin_view(self.add_crypto),
                name="add_crypto",
            ),
        ]
        return custom_urls + urls

    def add_crypto(self, request):
        from django.shortcuts import render, redirect

        if request.method == "POST":
            form = AddCryptoForm(request.POST)
            if form.is_valid():
                pair_symbol = form.cleaned_data["symbol"].upper()

                try:
                    # 🔥 Create from symbol or fetch existing
                    asset = CryptoSyncService.create_from_symbol(pair_symbol)

                    self.message_user(
                        request,
                        f"Crypto {pair_symbol} added successfully.",
                        messages.SUCCESS,
                    )
                    return redirect("admin:assets_asset_change", asset.id)

                except Exception as e:
                    self.message_user(
                        request,
                        f"Failed to add crypto {pair_symbol}: {e}",
                        messages.ERROR,
                    )

        else:
            form = AddCryptoForm()

        return render(
            request,
            "admin/add_crypto.html",
            {"form": form, "title": "Add Crypto by Symbol"},
        )
