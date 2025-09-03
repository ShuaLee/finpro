from django.contrib import admin
from schemas.models import SchemaColumnValue


@admin.register(SchemaColumnValue)
class SchemaColumnValueAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "get_schema",
        "get_column_title",
        "value",
        "get_account",
        "get_user_email",
        "is_edited",
    )
    list_filter = ("column__schema", "is_edited")
    search_fields = (
        "column__title",
        "value",
        "column__schema__name",
    )
    autocomplete_fields = ("column",)
    readonly_fields = ("account_ct", "account_id")

    def get_queryset(self, request):
        # optimize queries for related schema/column
        qs = super().get_queryset(request)
        return qs.select_related("column", "column__schema")

    # --- Custom columns ---
    def get_schema(self, obj):
        return obj.column.schema.name if obj.column and obj.column.schema else "(no schema)"
    get_schema.short_description = "Schema"

    def get_column_title(self, obj):
        return obj.column.title if obj.column else "(no column)"
    get_column_title.short_description = "Column"

    def get_account(self, obj):
        try:
            return str(obj.account) if obj.account else "(no account)"
        except Exception as e:
            return f"(err: {e})"
    get_account.short_description = "Account"

    def get_user_email(self, obj):
        try:
            target = obj.account
            if not target:
                return "(no account)"

            # Try multiple relationship paths
            if hasattr(target, "account") and hasattr(target.account, "stock_portfolio"):
                return target.account.stock_portfolio.portfolio.profile.user.email
            elif hasattr(target, "account") and hasattr(target.account, "precious_metal_portfolio"):
                return target.account.precious_metal_portfolio.portfolio.profile.user.email
            elif hasattr(target, "portfolio"):
                return target.portfolio.profile.user.email
            return "(no user)"
        except Exception as e:
            return f"(err: {e})"
    get_user_email.short_description = "User Email"
