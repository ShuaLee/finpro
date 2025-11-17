# schemas/services/schema_manager.py

from schemas.models.schema import Schema, SchemaColumnValue
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.services.schema_generator import SchemaGenerator


class SchemaManager:
    """
    Manages a schema and keeps SCVs (SchemaColumnValues) in sync with the schema.
    - Holding values remain RAW, untouched, unrounded.
    - SCVs represent formatted display values derived from schema rules.
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
    # Ensure Schema Exists
    # ============================================================
    @staticmethod
    def ensure_for_account(account):
        schema = Schema.objects.filter(
            portfolio=account.portfolio,
            account_type=account.account_type
        ).first()

        if schema:
            return schema

        generator = SchemaGenerator(account.portfolio, account.domain_type)
        schemas = generator.initialize()
        return next(
            (s for s in schemas if s.account_type == account.account_type),
            None
        )

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
        """
        Ensures every SchemaColumn has an SCV for this holding.
        SCVs created from raw holding values → formatted using schema rules.
        """

        existing = set(
            SchemaColumnValue.objects.filter(holding=holding)
            .values_list("column_id", flat=True)
        )

        missing = [col for col in self.columns if col.id not in existing]

        # Create missing SCVs
        new_scvs = []
        for col in missing:
            display_value = SchemaColumnValueManager.display_for_column(
                col, holding)

            new_scvs.append(
                SchemaColumnValue(
                    column=col,
                    holding=holding,
                    value=display_value,
                    is_edited=False,
                )
            )

        if new_scvs:
            SchemaColumnValue.objects.bulk_create(new_scvs)

        # Refresh all unedited SCVs (editable ones left alone)
        scvs = SchemaColumnValue.objects.filter(
            holding=holding,
            is_edited=False
        ).select_related("column")

        for scv in scvs:
            new_val = SchemaColumnValueManager.display_for_column(
                scv.column, holding)
            if scv.value != new_val:
                scv.value = new_val
                scv.save(update_fields=["value"])

    # ============================================================
    # Ensure SCVs for all holdings in an account
    # ============================================================

    def ensure_for_all_holdings(self, account):
        for holding in account.holdings.all():
            self.ensure_for_holding(holding)

    # ============================================================
    # Sync SCVs — Refreshes display values only
    # ============================================================
    def sync_for_holding(self, holding):
        """
        Recompute SCV display values. 
        Does NOT override edited SCVs.
        """
        for col in self.columns:
            scv = SchemaColumnValue.objects.filter(
                column=col, holding=holding).first()
            if scv:
                if not scv.is_edited:
                    manager = SchemaColumnValueManager(scv)
                    manager.refresh_display_value()
                    scv.save(update_fields=["value", "is_edited"])
            else:
                # If missing, ensure it
                self.ensure_for_holding(holding)

    def sync_for_all_holdings(self, account):
        for holding in account.holdings.all():
            self.sync_for_holding(holding)

    # ============================================================
    # FULL REFRESH (Force-resync everything including edited SCVs)
    # ============================================================
    def refresh_all(self, account):
        """
        Force recompute of all SCV display values using raw holding values.
        All SCVs become unedited.
        """
        for holding in account.holdings.all():
            for col in self.columns:
                scv = SchemaColumnValue.objects.filter(
                    column=col, holding=holding).first()
                if not scv:
                    continue

                manager = SchemaColumnValueManager(scv)
                manager.refresh_display_value()
                scv.save(update_fields=["value", "is_edited"])

    # ============================================================
    # Column-level management
    # ============================================================
    def on_column_added(self, column, account):
        """Ensure all holdings receive a new SCV when a column is added."""
        holdings = account.holdings.all()
        new_scvs = []

        for holding in holdings:
            exists = SchemaColumnValue.objects.filter(
                column=column, holding=holding
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
        """Remove all SCVs for a deleted column."""
        SchemaColumnValue.objects.filter(column=column).delete()

    # ============================================================
    # Resequencing columns
    # ============================================================
    def resequence_for_schema(self, schema):
        """
        Reassign display_order to be sequential without gaps.
        """
        columns = schema.columns.order_by("display_order", "id")

        for i, col in enumerate(columns, start=1):
            if col.display_order != i:
                col.display_order = i
                col.save(update_fields=["display_order"])
