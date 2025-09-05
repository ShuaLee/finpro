# from django.contrib import admin
# from accounts.models.custom import CustomAccount

# @admin.register(CustomAccount)
# class CustomAccountAdmin(admin.ModelAdmin):
#     list_display = ("name", "get_user_email", "custom_portfolio", "depth", "created_at")
#     search_fields = ("name",)
#     autocomplete_fields = ["custom_portfolio", "parent"]
#     readonly_fields = ("created_at", "last_synced", "depth")
#     list_filter = ("depth",)

#     def get_user_email(self, obj):
#         return obj.custom_portfolio.portfolio.profile.user.email
#     get_user_email.short_description = "User Email"
