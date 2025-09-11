from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from assets.models.holding import Holding


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "account",
        "asset",
        "quantity",
        "purchase_price",
        "purchase_date",
        "created_at",
    )
    list_filter = ("account__subportfolio__type", "purchase_date", "created_at")
    search_fields = (
        "asset__symbol",
        "asset__name",
        "account__name",
        "account__subportfolio__portfolio__profile__user__email",
    )
    autocomplete_fields = ("account", "asset")  # ✅ works now with AssetAdmin
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    def save_model(self, request, obj, form, change):
        try:
            obj.full_clean()
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            self.message_user(request, f"❌ {e}", level=messages.ERROR)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "account",
            "asset",
            "account__subportfolio",
            "account__subportfolio__portfolio",
            "account__subportfolio__portfolio__profile__user",
        )
