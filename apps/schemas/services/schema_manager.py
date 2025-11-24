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
        Ensure every SchemaColumn has an SCV for this holding.
        Rules:
        - Holding-backed SCVs are ALWAYS recalculated (and never edited).
        - Formula SCVs are ALWAYS recalculated (and never edited).
        - Asset/custom SCVs only refresh if is_edited=False.
        """

        from schemas.models.schema import SchemaColumnValue
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

            # -------------------------
            # 1️⃣ Holding-backed columns
            # -------------------------
            if col.source == "holding":
                manager.scv.is_edited = False
                manager.refresh_display_value()
                manager.scv.save(update_fields=["value", "is_edited"])
                continue

            # -------------------------
            # 2️⃣ Formula columns
            # -------------------------
            if col.source == "formula":
                manager.scv.is_edited = False
                manager.refresh_display_value()
                manager.scv.save(update_fields=["value", "is_edited"])
                continue

            # -------------------------
            # 3️⃣ Asset / Custom columns
            # -------------------------
            if not scv.is_edited:
                manager.refresh_display_value()
                manager.scv.save(update_fields=["value", "is_edited"])

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
        Refresh SCV display values without corrupting user edits.
        - Holding-backed SCVs always auto-sync and are never edited.
        - Asset/custom editable SCVs only update if !is_edited.
        - Formula SCVs always recompute.
        """
        for col in self.columns:
            scv = SchemaColumnValue.objects.filter(
                column=col,
                holding=holding
            ).first()

            if not scv:
                # ensure SCV exists
                self.ensure_for_holding(holding)
                continue

            manager = SchemaColumnValueManager(scv)

            # 1️⃣ Holding-backed columns → ALWAYS refresh, never edited
            if col.source == "holding":
                manager.scv.is_edited = False
                manager.refresh_display_value()
                manager.scv.save(update_fields=["value", "is_edited"])
                continue

            # 2️⃣ Formula columns → ALWAYS refresh
            if col.source == "formula":
                manager.scv.is_edited = False
                manager.refresh_display_value()
                manager.scv.save(update_fields=["value", "is_edited"])
                continue

            # 3️⃣ Asset/custom → refresh only if not edited
            if not scv.is_edited:
                manager.refresh_display_value()
                manager.scv.save(update_fields=["value", "is_edited"])

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
