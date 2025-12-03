import nested_admin
from accounts.models.account import Account


class AccountInline(nested_admin.NestedTabularInline):
    model = Account
    fk_name = "portfolio"
    extra = 0
    show_change_link = True

    fields = (
        "name",
        "account_type",
        "broker",
        "classification",
        "created_at",
        "last_synced",
    )

    readonly_fields = ("created_at", "last_synced")
