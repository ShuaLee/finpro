from schemas.models.account_column_visibility import AccountColumnVisibility


class AccountColumnVisibilityService:
    """
    Handles initialization and management of per-account column visibility.
    """

    @staticmethod
    def initialize_for_schema_column(*, column):
        """
        Create visibility rows for ALL accounts that use this column's schema.
        Called when a new SchemaColumn is created.
        """
        accounts = column.schema.portfolio.accounts.filter(
            account_type=column.schema.account_type
        )

        AccountColumnVisibility.objects.bulk_create(
            [
                AccountColumnVisibility(
                    account=account,
                    column=column,
                    is_visible=True,
                )
                for account in accounts
            ],
            ignore_conflicts=True,
        )

    @staticmethod
    def initialize_for_account(*, account):
        """
        Create visibility rows for ALL columns in the account's schema.
        Called when a new Account is created.
        """
        from schemas.services.schema_manager import SchemaManager
        
        schema = SchemaManager.ensure_for_account(account)

        AccountColumnVisibility.objects.bulk_create(
            [
                AccountColumnVisibility(
                    account=account,
                    column=column,
                    is_visible=True,
                )
                for column in schema.columns.all()
            ],
            ignore_conflicts=True,
        )

    # --------------------------------------------------
    # VISIBILITY MUTATIONS
    # --------------------------------------------------
    @staticmethod
    def set_visibility(*, account, column, is_visible: bool):
        """
        Explicitly set visibility for a column on an account.
        """
        AccountColumnVisibility.objects.update_or_create(
            account=account,
            column=column,
            defaults={"is_visible": is_visible},
        )

    @staticmethod
    def hide_column(*, account, column):
        AccountColumnVisibilityService.set_visibility(
            account=account,
            column=column,
            is_visible=False,
        )

    @staticmethod
    def show_column(*, account, column):
        AccountColumnVisibilityService.set_visibility(
            account=account,
            column=column,
            is_visible=True,
        )

    @staticmethod
    def reset_account_to_defaults(*, account):
        """
        Reset ALL column visibility for an account to visible.
        """
        AccountColumnVisibility.objects.filter(
            account=account
        ).update(is_visible=True)