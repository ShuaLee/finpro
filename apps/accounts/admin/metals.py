from django.contrib import admin
from accounts.models.metals import StorageFacility

@admin.register(StorageFacility)
class StorageFacilityAdmin(admin.ModelAdmin):
    list_display = (
        "name", "get_user_email", "metal_portfolio", "is_insured",
        "is_lending_account", "interest_rate", "created_at"
    )
    list_filter = ("is_insured", "is_lending_account")
    search_fields = ("name",)
    autocomplete_fields = ["metal_portfolio"]
    readonly_fields = ("created_at", "last_synced")

    def get_user_email(self, obj):
        return obj.metal_portfolio.portfolio.profile.user.email
    get_user_email.short_description = "User Email"