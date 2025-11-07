from schemas.models.schema import Schema, SchemaColumnValue
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.services.schema_generator import SchemaGenerator


class SchemaManager:
    """
    Manages a schema and its relationship to holdings + SchemaColumnValues (SCVs).
    """

    def __init__(self, schema):
        self.schema = schema
        self._columns = None  # cache placeholder

    # -------------------------------
    # Cached access
    # -------------------------------
    @property
    def columns(self):
        """Cache schema columns for performance across multiple operations."""
        if self._columns is None:
            self._columns = list(self.schema.columns.all())
        return self._columns

    # -------------------------------
    # Schema ensuring
    # -------------------------------
    @staticmethod
    def ensure_for_account(account):
        """
        Ensure a schema exists for this account's (portfolio, account_type).
        If not, build it from the domain’s schema config.
        """
        portfolio = account.portfolio
        domain_type = account.domain_type

        existing = Schema.objects.filter(
            portfolio=portfolio,
            account_type=account.account_type
        ).first()

        if existing:
            return existing

        # Generate a new schema for this domain/account_type
        generator = SchemaGenerator(portfolio, domain_type)
        return generator.initialize()

    @classmethod
    def for_account(cls, account):
        schema = account.active_schema
        if not schema:
            raise ValueError(
                f"No active schema for account {account.name} "
                f"(portfolio={account.portfolio.id}, account_type={account.account_type})"
            )
        return cls(schema)

    # -------------------------------
    # SCV creation / ensuring
    # -------------------------------
    def ensure_for_holding(self, holding):
        """
        Ensure all SCVs exist for this holding.
        Optimized to bulk-create missing SCVs in one go.
        """
        existing_ids = SchemaColumnValue.objects.filter(
            holding=holding
        ).values_list("column_id", flat=True)

        # Find missing columns for this holding
        missing_cols = [
            col for col in self.columns if col.id not in existing_ids]

        # Bulk create all missing SCVs
        to_create = [
            SchemaColumnValue(
                column=col,
                holding=holding,
                value=SchemaColumnValueManager.default_for_column(
                    col, holding),
                is_edited=False,
            )
            for col in missing_cols
        ]
        if to_create:
            SchemaColumnValue.objects.bulk_create(to_create)

        # Refresh all non-edited SCVs to reflect updated defaults
        editable_scvs = SchemaColumnValue.objects.filter(
            holding=holding, is_edited=False
        ).select_related("column")

        for scv in editable_scvs:
            new_val = SchemaColumnValueManager.default_for_column(
                scv.column, holding)
            if scv.value != new_val:
                scv.value = new_val
                scv.save(update_fields=["value"])

    def ensure_for_all_holdings(self, account):
        """Ensure SCVs for every holding in this account."""
        for holding in account.holdings.all():
            self.ensure_for_holding(holding)

    # -------------------------------
    # SCV syncing
    # -------------------------------
    def sync_for_holding(self, holding):
        for col in self.columns:
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
        """Force-resync all SCVs (ignoring edit flags)."""
        for holding in account.holdings.all():
            for col in self.columns:
                scv = SchemaColumnValue.objects.filter(
                    column=col, holding=holding).first()
                if scv:
                    SchemaColumnValueManager(scv).reset_to_source()

    # -------------------------------
    # Column-level operations
    # -------------------------------
    def on_column_added(self, column, account):
        """Ensure all holdings have a new SCV for a newly added column."""
        holdings = account.holdings.all()
        to_create = []
        for holding in holdings:
            if not SchemaColumnValue.objects.filter(column=column, holding=holding).exists():
                to_create.append(
                    SchemaColumnValue(
                        column=column,
                        holding=holding,
                        value=SchemaColumnValueManager.default_for_column(
                            column, holding),
                        is_edited=False,
                    )
                )
        if to_create:
            SchemaColumnValue.objects.bulk_create(to_create)

    def on_column_deleted(self, column):
        """Delete all SCVs linked to a deleted column."""
        SchemaColumnValue.objects.filter(column=column).delete()

    def resequence_for_schema(self, schema):
        columns = schema.columns.order_by("display_order", "id")
        for index, col in enumerate(columns, start=1):
            if col.display_order != index:
                col.display_order = index
                col.save(update_fields=["display_order"])
