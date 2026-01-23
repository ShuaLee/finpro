from schemas.models.schema import Schema, SchemaColumnValue
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.services.schema_generator import SchemaGenerator


def _can_recompute(scv: SchemaColumnValue) -> bool:
    """
    SCVs created or modified by the user must never be recomputed.
    """
    return scv.source != SchemaColumnValue.SOURCE_USER


class SchemaManager:
    """
    INTERNAL schema execution engine.

    Responsibilities:
        - Ensure SchemaColumnValues (SCVs) exist
        - Recompute SCVs deterministically
        - Preserve user overrides

    IMPORTANT:
        ❗ This class MUST NOT be called directly by domain code.
        ❗ All recomputation must be routed via SCVRefreshService.
    """

    def __init__(self, schema: Schema):
        self.schema = schema
        self._columns_cache = None

    # ============================================================
    # Schema bootstrap (PUBLIC)
    # ============================================================
    @staticmethod
    def ensure_for_account(account):
        """
        Ensure a schema exists for the given account.
        """
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
        """
        INTERNAL factory.
        Used ONLY by SCVRefreshService.
        """
        schema = account.active_schema
        if not schema:
            raise ValueError(
                f"No active schema for account '{account.name}' "
                f"(portfolio={account.portfolio.id}, "
                f"account_type={account.account_type})"
            )
        return cls(schema)

    # ============================================================
    # Cached columns (INTERNAL)
    # ============================================================
    @property
    def _columns(self):
        if self._columns_cache is None:
            self._columns_cache = list(self.schema.columns.all())
        return self._columns_cache

    # ============================================================
    # CORE RECOMPUTE PRIMITIVE (INTERNAL)
    # ============================================================
    def _recompute_scv(self, scv: SchemaColumnValue, column):
        """
        Recompute a single SCV if allowed.
        """
        if not _can_recompute(scv):
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
    # HOLDING RECOMPUTE (INTERNAL)
    # ============================================================
    def sync_for_holding(self, holding):
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
                    "source": SchemaColumnValue.SOURCE_SYSTEM,
                },
            )

            self._recompute_scv(scv, column)

    # ============================================================
    # COLUMN LIFECYCLE HELPERS (INTERNAL)
    # ============================================================
    def ensure_column_values(self, column):
        """
        Ensure SCVs exist for a newly added column.
        """
        accounts = self.schema.portfolio.accounts.filter(
            account_type=self.schema.account_type
        ).prefetch_related("holdings")

        new_scvs = []

        for account in accounts:
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

    def delete_column_values(self, column):
        """
        Remove all SCVs for a deleted column.
        """
        SchemaColumnValue.objects.filter(column=column).delete()

    # ============================================================
    # Resequencing (INTERNAL)
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
