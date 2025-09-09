from schemas.models import SchemaColumnValue
from schemas.services.schema_column_value_manager import SchemaColumnValueManager


class SchemaManager:
    """
    Manages a schema and its relationship to holdings + SchemaColumnValues (SCVs).
    """

    def __init__(self, schema):
        self.schema = schema

    @classmethod
    def for_account(cls, account):
        schema = account.active_schema
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
        for col in self.schema.columns.all():
            scv, created = SchemaColumnValue.objects.get_or_create(
                column=col,
                holding=holding,
                defaults={
                    "value": SchemaColumnValueManager.default_for_column(col, holding),
                    "is_edited": False,
                },
            )

            if not created and not scv.is_edited:
                scv.value = SchemaColumnValueManager.default_for_column(
                    col, holding)
                scv.save(update_fields=["value"])

    def ensure_for_all_holdings(self, account):
        """
        Ensure SCVs for every holding in this account.
        """
        for holding in account.holdings.all():
            self.ensure_for_holding(holding)

    # -------------------------------
    # SCV syncing
    # -------------------------------
    def sync_for_holding(self, holding):
        for col in self.schema.columns.all():
            scv = SchemaColumnValue.objects.filter(
                column=col, holding=holding).first()
            if scv:
                SchemaColumnValueManager(scv).reset_to_source()
            else:
                self.ensure_for_holding(holding)

    def sync_for_all_holdings(self, account):
        for holding in account.holdings.all():
            self.sync_for_holding(holding)

    def refresh_all(self, account):
        """
        Force-resync all SCVs (ignoring edit flags).
        """
        for holding in account.holdings.all():
            for col in self.schema.columns.all():
                scv = SchemaColumnValue.objects.filter(
                    column=col, holding=holding).first()
                if scv:
                    SchemaColumnValueManager(scv).reset_to_source()

    # -------------------------------
    # Column-level operations
    # -------------------------------
    def on_column_added(self, column, account):
        for holding in account.holdings.all():
            SchemaColumnValue.objects.get_or_create(
                column=column,
                holding=holding,
                defaults={
                    "value": SchemaColumnValueManager.default_for_column(column, holding),
                    "is_edited": False,
                },
            )

    def on_column_deleted(self, column):
        SchemaColumnValue.objects.filter(column=column).delete()
