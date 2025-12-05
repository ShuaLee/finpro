# schemas/services/schema_manager.py

from schemas.models.schema import Schema, SchemaColumnValue
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.services.schema_generator import SchemaGenerator


class SchemaManager:
    """
    Manages a schema and keeps SCVs (SchemaColumnValues) in sync with the schema.
    - Holding values remain RAW.
    - SCVs are formatted display values.
    """

    def __init__(self, schema):
        self.schema = schema
        self._columns_cache = None

    # ============================================================
    # Cached Columns
    # ============================================================
    @property
    def columns(self):
        if self._columns_cache is None:
            self._columns_cache = list(self.schema.columns.all())
        return self._columns_cache

    # ============================================================
    # Ensure Schema Exists for an Account
    # ============================================================
    @staticmethod
    def ensure_for_account(account):
        """
        Schema is keyed by:
        - portfolio
        - account_type  (FK)
        """

        schema = Schema.objects.filter(
            portfolio=account.portfolio,
            account_type=account.account_type
        ).first()

        if schema:
            return schema

        # ❗ FIXED — remove domain_type, pass AccountType instead
        generator = SchemaGenerator(
            portfolio=account.portfolio,
            domain_type=account.account_type  # correct: pass FK object
        )

        schemas = generator.initialize()

        # return only the schema matching this account_type
        return next(
            (s for s in schemas if s.account_type == account.account_type),
            None
        )

    # ============================================================
    # Wrapper to get a SchemaManager from an account
    # ============================================================
    @classmethod
    def for_account(cls, account):
        schema = account.active_schema
        if not schema:
            raise ValueError(
                f"No active schema for account '{account.name}' "
                f"(portfolio={account.portfolio.id}, account_type={account.account_type})"
            )
        return cls(schema)

    # ============================================================
    # Ensure SCVs Exist for Holding
    # ============================================================
    def ensure_for_holding(self, holding):
        from schemas.services.schema_column_value_manager import SchemaColumnValueManager

        for col in self.columns:

            scv, created = SchemaColumnValue.objects.get_or_create(
                column=col,
                holding=holding,
                defaults={
                    "value": SchemaColumnValueManager.display_for_column(col, holding),
                    "is_edited": False,
                }
            )

            manager = SchemaColumnValueManager(scv)

            # holding-backed
            if col.source == "holding":
                manager.scv.is_edited = False
                manager.refresh_display_value()
                manager.scv.save(update_fields=["value", "is_edited"])
                continue

            # formula
            if col.source == "formula":
                manager.scv.is_edited = False
                manager.refresh_display_value()
                manager.scv.save(update_fields=["value", "is_edited"])
                continue

            # asset or custom
            if not scv.is_edited:
                manager.refresh_display_value()
                manager.scv.save(update_fields=["value", "is_edited"])

    # ============================================================
    # Ensure SCVs for all holdings
    # ============================================================
    def ensure_for_all_holdings(self, account):
        for holding in account.holdings.all():
            self.ensure_for_holding(holding)

    # ============================================================
    # Sync SCVs — only non-edited fields update
    # ============================================================
    def sync_for_holding(self, holding):
        for col in self.columns:
            scv = SchemaColumnValue.objects.filter(
                column=col, holding=holding
            ).first()

            if not scv:
                self.ensure_for_holding(holding)
                continue

            manager = SchemaColumnValueManager(scv)

            if col.source == "holding":
                manager.scv.is_edited = False
                manager.refresh_display_value()
                manager.scv.save(update_fields=["value", "is_edited"])
                continue

            if col.source == "formula":
                manager.scv.is_edited = False
                manager.refresh_display_value()
                manager.scv.save(update_fields=["value", "is_edited"])
                continue

            if not scv.is_edited:
                manager.refresh_display_value()
                manager.scv.save(update_fields=["value", "is_edited"])

    def sync_for_all_holdings(self, account):
        for holding in account.holdings.all():
            self.sync_for_holding(holding)

    # ============================================================
    # Full refresh — resets all SCVs
    # ============================================================
    def refresh_all(self, account):
        for holding in account.holdings.all():
            for col in self.columns:
                scv = SchemaColumnValue.objects.filter(
                    column=col, holding=holding
                ).first()
                if not scv:
                    continue

                manager = SchemaColumnValueManager(scv)
                manager.refresh_display_value()
                scv.save(update_fields=["value", "is_edited"])

    # ============================================================
    # Column add / remove
    # ============================================================
    def on_column_added(self, column, account):
        holdings = account.holdings.all()
        new_scvs = []

        for holding in holdings:
            exists = SchemaColumnValue.objects.filter(
                column=column,
                holding=holding
            ).exists()

            if not exists:
                new_scvs.append(
                    SchemaColumnValue(
                        column=column,
                        holding=holding,
                        value=SchemaColumnValueManager.display_for_column(
                            column, holding),
                        is_edited=False,
                    )
                )

        if new_scvs:
            SchemaColumnValue.objects.bulk_create(new_scvs)

    def on_column_deleted(self, column):
        SchemaColumnValue.objects.filter(column=column).delete()

    # ============================================================
    # Resequencing
    # ============================================================
    def resequence_for_schema(self, schema):
        columns = schema.columns.order_by("display_order", "id")

        for i, col in enumerate(columns, start=1):
            if col.display_order != i:
                col.display_order = i
                col.save(update_fields=["display_order"])
