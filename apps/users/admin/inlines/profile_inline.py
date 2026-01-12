# # users/admin/inlines/profile_inline.py

# import nested_admin
# from users.models import Profile
# from .portfolio_inline import PortfolioInline


# class ProfileInline(nested_admin.NestedStackedInline):
#     model = Profile
#     fk_name = "user"
#     extra = 0
#     max_num = 1
#     can_delete = False

#     inlines = [PortfolioInline]

#     fields = (
#         "full_name",
#         "country",
#         "currency",
#         "plan",
#         "account_type",
#     )

#     # DO NOT override has_add_permission for nested-admin
#     # It breaks rendering of existing parent objects
#     # and prevents child inlines from appearing.

#     def has_delete_permission(self, request, obj=None):
#         return False

#     class Media:
#         css = {"all": ("admin/hide_inline_add.css",)}
