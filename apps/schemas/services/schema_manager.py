from schemas.models import Schema, SchemaColumnValue
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.services.schema_generator import SchemaGenerator


def _can_recompute(scv: SchemaColumnValue) -> bool:
    """
    User-overridden SCVs must never be recomputed.
    """
    return scv.source != SchemaColumnValue.Source.USER


class SchemaManager:
    """
    Deterministic schema execution engine.

    Responsibilities:
        - Ensure SCVs exist
        - Recompute SCVs deterministically
        - Preserve user overrides

    ❗ This class MUST NOT be called directly by domain code.
    ❗ All calls must go through SCVRefreshService.
    """

    def __init__(self, schema: Schema):
        self.schema = schema
        self._columns_cache = None

    # ============================================================
    # FACTORIES
    # ============================================================
    @classmethod
    def for_account(cls, account):
        """
        INTERNAL factory.
        Used ONLY by SCVRefreshService.
        """
        schema = getattr(account, "active_schema", None)
        if not schema:
            raise ValueError(
                f"No active schema for account '{account}'."
            )
        return cls(schema)

    @staticmethod
    def ensure_for_account(account):
        """
        Ensure a schema exists for an account.
        Used during account creation / access.
        """
        schema = Schema.objects.filter(
            portfolio=account.portfolio,
            account_type=account.account_type,
        ).first()

        if schema:
            return schema

        generator = SchemaGenerator(
            portfolio=account.portfolio,
            account_type=account.account_type,
        )
        schema = generator.initialize()

        return schema

    # ============================================================
    # INTERNAL HELPERS
    # ============================================================
    @property
    def _columns(self):
        if self._columns_cache is None:
            self._columns_cache = list(self.schema.columns.all())
        return self._columns_cache

    # ============================================================
    # CORE EXECUTION
    # ============================================================
    def sync_scvs_for_holding(self, holding):
        """
        Recompute all SCVs for a single holding.

        CALLED ONLY BY SCVRefreshService.
        """
        for column in self._columns:
            scv, _ = SchemaColumnValue.objects.get_or_create(
                column=column,
                holding=holding,
                defaults={
                    "value": SchemaColumnValueManager.display_for_column(
                        column, holding
                    ),
                    "source": SchemaColumnValue.Source.SYSTEM,
                },
            )
            self._recompute_scv(scv, column)

    def _recompute_scv(self, scv: SchemaColumnValue, column):
        """
        Recompute a single SCV if allowed.
        """
        if not _can_recompute(scv):
            return

        manager = SchemaColumnValueManager(scv)
        manager.refresh_display_value()

        asset = scv.holding.asset if scv.holding else None
        asset_type = asset.asset_type if asset else None

        behavior = (
            column.behavior_for(asset_type)
            if asset_type else None
        )

        if behavior and behavior.source == "formula":
            scv.source = SchemaColumnValue.Source.FORMULA
        else:
            scv.source = SchemaColumnValue.Source.SYSTEM

        scv.save(update_fields=["value", "source"])

    # ============================================================
    # COLUMN LIFECYCLE (INTERNAL)
    # ============================================================

    def ensure_column_values(self, column):
        """
        Ensure SCVs exist for a newly added column.
        Delegates to SchemaColumnValueManager.
        """
        SchemaColumnValueManager.ensure_for_column(column)

    def delete_column_values(self, column):
        """
        Remove all SCVs for a deleted column.
        """
        SchemaColumnValue.objects.filter(column=column).delete()

    # ============================================================
    # ORDER NORMALIZATION
    # ============================================================
    def resequence(self):
        """
        Normalize display_order for schema columns.
        """
        for i, col in enumerate(
            self.schema.columns.order_by("display_order", "id"),
            start=1,
        ):
            if col.display_order != i:
                col.display_order = i
                col.save(update_fields=["display_order"])
