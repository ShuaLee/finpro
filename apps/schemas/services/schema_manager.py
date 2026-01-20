from schemas.models.schema import Schema, SchemaColumnValue
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.services.schema_generator import SchemaGenerator


def can_recompute(scv: SchemaColumnValue) -> bool:
    """
    SCVs created or modified by the user must never be recomputed.
    """
    return scv.source != SchemaColumnValue.SOURCE_USER


class SchemaManager:
    """
    Manages a schema and keeps SchemaColumnValues (SCVs) in sync.

    - Holding + asset values are RAW
    - SCVs are formatted display values
    - User edits are preserved
    """

    def __init__(self, schema: Schema):
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
    # Schema bootstrap
    # ============================================================
    @staticmethod
    def ensure_for_account(account):
        schema = Schema.objects.filter(
            portfolio=account.portfolio,
            account_type=account.account_type,
        ).first()

        if schema:
            return schema

        generator = SchemaGenerator(
            portfolio=account.portfolio,
            domain_type=account.account_type,
        )

        schemas = generator.initialize()

        return next(
            (s for s in schemas if s.account_type == account.account_type),
            None,
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
    # Core SCV recompute primitive (THE ONLY ONE)
    # ============================================================
    def _recompute_scv(self, scv: SchemaColumnValue, column):
        if not can_recompute(scv):
            return

        manager = SchemaColumnValueManager(scv)
        manager.refresh_display_value()

        scv.source = (
            SchemaColumnValue.SOURCE_FORMULA
            if column.source == "formula"
            else SchemaColumnValue.SOURCE_SYSTEM
        )

        scv.save(update_fields=["value", "source"])

    # ============================================================
    # Ensure SCVs for holding
    # ============================================================
    def ensure_for_holding(self, holding):
        for col in self.columns:
            scv, _ = SchemaColumnValue.objects.get_or_create(
                column=col,
                holding=holding,
                defaults={
                    "value": SchemaColumnValueManager.display_for_column(
                        col, holding
                    ),
                    "source": SchemaColumnValue.SOURCE_SYSTEM,
                },
            )

            self._recompute_scv(scv, col)

    def ensure_for_all_holdings(self, account):
        for holding in account.holdings.all():
            self.ensure_for_holding(holding)

    # ============================================================
    # Sync (called on holding updates)
    # ============================================================
    def sync_for_holding(self, holding):
        for col in self.columns:
            scv = SchemaColumnValue.objects.filter(
                column=col,
                holding=holding,
            ).first()

            if not scv:
                self.ensure_for_holding(holding)
                continue

            self._recompute_scv(scv, col)

    def sync_for_all_holdings(self, account):
        for holding in account.holdings.all():
            self.sync_for_holding(holding)

    # ============================================================
    # Full refresh (schema-wide)
    # ============================================================
    def refresh_all(self, account):
        for holding in account.holdings.all():
            for col in self.columns:
                scv = SchemaColumnValue.objects.filter(
                    column=col,
                    holding=holding,
                ).first()

                if scv:
                    self._recompute_scv(scv, col)

    # ============================================================
    # Column lifecycle
    # ============================================================
    def on_column_added(self, column, account):
        new_scvs = []

        for holding in account.holdings.all():
            if not SchemaColumnValue.objects.filter(
                column=column,
                holding=holding,
            ).exists():
                new_scvs.append(
                    SchemaColumnValue(
                        column=column,
                        holding=holding,
                        value=SchemaColumnValueManager.display_for_column(
                            column, holding
                        ),
                        source=SchemaColumnValue.SOURCE_SYSTEM,
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
