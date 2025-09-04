from django.contrib.contenttypes.models import ContentType
from schemas.models import SchemaColumnValue
from schemas.services.schema_column_value_manager import SchemaColumnValueManager


class SchemaManager:
    """
    Manages a schema and its relationship to holdings + SCVs.
    """

    def __init__(self, schema):
        self.schema = schema

    @classmethod
    def for_account(cls, account):
        schema = account.get_active_schema()
        if not schema:
            raise ValueError(f"No active schema for account {account}")
        return cls(schema)

    # -------------------------------
    # SCV creation / ensuring
    # -------------------------------
    def ensure_for_holding(self, holding):
        """
        Ensure all SCVs exist for this holding.
        """
        from schemas.services.schema_column_value_manager import SchemaColumnValueManager
        ct = ContentType.objects.get_for_model(holding.__class__)

        for col in self.schema.columns.all():
            scv, created = SchemaColumnValue.objects.get_or_create(
                column=col,
                account_ct=ct,
                account_id=holding.id,
                defaults={
                    "value": SchemaColumnValueManager.default_for_column(col, holding),
                    "is_edited": False,
                },
            )

            if not created:
                # Re-sync value from source if not edited
                if not scv.is_edited:
                    scv.value = SchemaColumnValueManager.default_for_column(col, holding)
                    scv.save(update_fields=["value"])

    def ensure_for_all_holdings(self, account):
        """
        Ensure all SCVs exist for every holding in this account.
        """
        for holding in account.holdings.all():
            self.ensure_for_holding(holding)

    # -------------------------------
    # SCV syncing
    # -------------------------------
    def sync_for_holding(self, holding):
        """
        Sync all SCVs for a single holding.
        """
        ct = ContentType.objects.get_for_model(holding.__class__)
        for col in self.schema.columns.all():
            scv = SchemaColumnValue.objects.filter(
                column=col,
                account_ct=ct,
                account_id=holding.id,
            ).first()
            if scv:
                SchemaColumnValueManager(scv).reset_to_source()
            else:
                self.ensure_for_holding(holding)

    def sync_for_all_holdings(self, account):
        """
        Sync all SCVs for all holdings in this account.
        """
        for holding in account.holdings.all():
            self.sync_for_holding(holding)

    # -------------------------------
    # Column-level operations
    # -------------------------------
    def on_column_added(self, column, account):
        """
        When a new SchemaColumn is added, backfill SCVs for all holdings.
        """
        ct = ContentType.objects.get_for_model(account.holdings.model)
        for holding in account.holdings.all():
            SchemaColumnValue.objects.get_or_create(
                column=column,
                account_ct=ct,
                account_id=holding.id,
                defaults={
                    "value": SchemaColumnValueManager.default_for_column(column, holding),
                    "is_edited": False,
                },
            )

    def on_column_deleted(self, column):
        """
        When a column is deleted, remove all its SCVs.
        """
        SchemaColumnValue.objects.filter(column=column).delete()
