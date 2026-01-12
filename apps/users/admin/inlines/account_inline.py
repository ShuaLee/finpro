# import nested_admin

# from accounts.models.account import Account
# from .holding_inline import HoldingInline
# from .schema_inline import SchemaPreviewMixin


# class AccountInline(SchemaPreviewMixin, nested_admin.NestedStackedInline):
#     model = Account
#     fk_name = "portfolio"
#     extra = 0
#     show_change_link = True

#     fieldsets = (
#         (
#             "Account Information",
#             {
#                 "fields": (
#                     "name",
#                     "account_type",
#                     "broker",
#                     "classification",
#                     "created_at",
#                     "last_synced",
#                 )
#             },
#         ),
#         SchemaPreviewMixin.schema_fieldset,  # ← add the schema panel
#     )

#     readonly_fields = (
#         "created_at",
#         "last_synced",
#         "schema_preview",
#         "schema_link",
#     )

#     inlines = [HoldingInline]
