import nested_admin
from portfolios.models.portfolio import Portfolio
from users.admin.inlines.account_inline import AccountInline


class PortfolioInline(nested_admin.NestedStackedInline):
    """
    Nested inline for Profile -> Portfolio
    """
    print("DEBUG: PortfolioInline loaded")
    print("DEBUG: PortfolioInline model FK:", Portfolio._meta.get_fields())
    print("DEBUG: PortfolioInline fk_name:", "profile")

    model = Portfolio
    fk_name = "profile"
    extra = 0
    can_delete = False

    readonly_fields = ("created_at",)

    fields = (
        "name",
        "is_main",
        "created_at",
    )

    inlines = [AccountInline]
