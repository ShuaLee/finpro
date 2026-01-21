from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError

from accounts.models.holding import Holding
from schemas.services.scv_refresh_service import SCVRefreshService


# =================================================
# Form
# =================================================

class HoldingAdminForm(forms.ModelForm):
    """
    Admin form for Holding.
    Enforces invariants via model.clean(), but adds UX hints.
    """

    class Meta:
        model = Holding
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()

        quantity = cleaned.get("quantity")
        avg_price = cleaned.get("average_purchase_price")

        if quantity == 0 and avg_price is not None:
            raise ValidationError(
                "Average purchase price must be empty when quantity is zero."
            )

        return cleaned


# =================================================
# Admin
# =================================================

@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    form = HoldingAdminForm

    list_display = (
        "id",
        "account",
        "asset",
        "source",
        "original_ticker",
        "custom_reason",
        "quantity",
        "average_purchase_price",
        "current_value_display",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "account__portfolio",
        "account__account_type",
        "asset__asset_type",
    )

    search_fields = (
        "asset__name",
        "asset__identifiers__value",
        "account__name",
        "account__portfolio__name",
    )

    ordering = (
        "account",
        "asset",
    )

    readonly_fields = (
        "original_ticker",
        "custom_reason",
        "created_at",
        "updated_at",
        "current_value_display",
    )

    autocomplete_fields = (
        "account",
        "asset",
    )

    fieldsets = (
        (None, {
            "fields": (
                "account",
                "asset",
            )
        }),
        ("Position", {
            "fields": (
                "quantity",
                "average_purchase_price",
                "current_value_display",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
        ("Sourcing", {
            "fields": (
                "source",
                "original_ticker",
                "custom_reason",
            )
        }),

    )

    # -------------------------------------------------
    # Display helpers
    # -------------------------------------------------
    def current_value_display(self, obj):
        value = obj.current_value
        return value if value is not None else "—"

    current_value_display.short_description = "Current Value"

    # -------------------------------------------------
    # Permissions
    # -------------------------------------------------
    def has_add_permission(self, request):
        """
        Allow creation via admin, but enforce uniqueness via model constraint.
        """
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # After save, trigger domain reactions
        SCVRefreshService.holding_changed(obj)
