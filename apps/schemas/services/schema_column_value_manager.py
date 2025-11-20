from schemas.services.formulas.update_engine import FormulaUpdateEngine

from decimal import Decimal, ROUND_HALF_UP


class SchemaColumnValueManager:
    """
    SCV Manager:
      - Holds display (formatted) values derived from Holding/raw values
      - Never mutates Holding values except when the user explicitly edits through SCV
      - Applies decimal_places, max_length, etc. to SCV display
      - Holding = raw truth (no rounding)
    """

    # ============================================================
    # INITIALIZATION
    # ============================================================
    def __init__(self, scv):
        from schemas.models.schema import SchemaColumnValue
        if not isinstance(scv, SchemaColumnValue):
            raise TypeError("Expected SchemaColumnValue instance")

        self.scv = scv
        self.column = scv.column
        self.holding = scv.holding

    # ============================================================
    # CREATE SCVs FOR HOLDING OR FOR COLUMN
    # ============================================================
    @classmethod
    def ensure_for_holding(cls, holding):
        schema = holding.active_schema
        if not schema:
            return

        for column in schema.columns.all():
            cls.get_or_create(holding, column)

    @classmethod
    def ensure_for_column(cls, column):
        """Every holding for accounts of this schema must get an SCV for this column."""
        schema = column.schema
        accounts = schema.portfolio.accounts.filter(
            account_type=schema.account_type
        )

        for account in accounts:
            for holding in account.holdings.all():
                cls.get_or_create(holding, column)

    @classmethod
    def refresh_for_holding(cls, holding):
        schema = holding.active_schema
        if not schema:
            return

        for column in schema.columns.all():
            mgr = cls.get_or_create(holding, column)
            mgr.refresh_display_value()
            mgr.scv.save(update_fields=["value", "is_edited"])

    @classmethod
    def get_or_create(cls, holding, column):
        from schemas.models.schema import SchemaColumnValue

        initial_value = cls.display_for_column(column, holding)

        scv, created = SchemaColumnValue.objects.get_or_create(
            column=column,
            holding=holding,
            defaults={"value": initial_value, "is_edited": False},
        )
        return cls(scv)

    # ============================================================
    # DISPLAY LOGIC
    # ============================================================
    @staticmethod
    def display_for_column(column, holding):
        """Compute display value using schema constraints."""

        raw_value = None

        # Holding field
        if column.source == "holding" and column.source_field:
            raw_value = SchemaColumnValueManager._resolve_path(
                holding, column.source_field
            )

        # Asset field
        elif column.source == "asset" and column.source_field:
            asset = getattr(holding, "asset", None)
            if asset:
                raw_value = SchemaColumnValueManager._resolve_path(
                    asset, column.source_field
                )

        # Static default
        if raw_value is None:
            return SchemaColumnValueManager._static_default(column)

        # Apply decimal_places, max_length, etc.
        return SchemaColumnValueManager._apply_display_constraints(
            column, raw_value, holding
        )

    def refresh_display_value(self):
        """Refresh formatted display value from raw value."""
        self.scv.value = self.display_for_column(self.column, self.holding)
        self.scv.is_edited = False

    # ============================================================
    # DISPLAY FORMATTING
    # ============================================================
    @staticmethod
    def _apply_display_constraints(column, raw_value, holding):
        dt = column.data_type

        # ---------- DECIMAL ----------
        if dt == "decimal":
            try:
                numeric = Decimal(str(raw_value))
            except:
                return raw_value

            dp = SchemaColumnValueManager._decimal_places_for_column(
                column, holding
            )
            quant = Decimal("1").scaleb(-dp)
            return str(numeric.quantize(quant, rounding=ROUND_HALF_UP))

        # ---------- STRING ----------
        if dt == "string":
            try:
                s = str(raw_value)
            except:
                return raw_value

            max_len = SchemaColumnValueManager._max_length_for_column(column)
            return s[:max_len] if max_len and len(s) > max_len else s

        # ---------- INTEGER ----------
        if dt == "integer":
            try:
                return str(int(raw_value))
            except:
                return raw_value

        return raw_value

    # ============================================================
    # DECIMAL PLACES WITH CRYPTO OVERRIDE
    # ============================================================
    @staticmethod
    def _decimal_places_for_column(column, holding=None):
        """
        Crypto quantity override:
        If holding.asset.crypto_detail.quantity_precision exists → use that.
        """
        if (
            holding is not None
            and column.schema.account_type == "crypto_wallet"
            and column.source == "holding"
            and column.source_field == "quantity"
        ):
            asset = getattr(holding, "asset", None)
            if asset and getattr(asset, "crypto_detail", None):
                return asset.crypto_detail.quantity_precision

        # Regular constraint fallback
        c = column.constraints_set.filter(name="decimal_places").first()
        return int(c.value or c.default_value or 2) if c else 2

    @staticmethod
    def _max_length_for_column(column):
        c = column.constraints_set.filter(name="max_length").first()
        return int(c.value or c.default_value or 255) if c else None

    # ============================================================
    # EDITING VALUES
    # ============================================================

    def _trigger_formula_updates(self):
        schema = self.scv.column.schema
        holding = self.scv.holding

        engine = FormulaUpdateEngine(holding, schema)
        engine.update_dependent_formulas(self.scv.column.identifier)

    def save_value(self, new_raw_value, is_edited: bool):
        """Save raw value (holding) or edited SCV."""

        # Holding-sourced column -> update the holding directly
        if self.column.source == "holding":
            casted = self._cast_raw_value(new_raw_value)
            setattr(self.holding, self.column.source_field, casted)
            self.holding.save(update_fields=[self.column.source_field])

            self.refresh_display_value()
            self.scv.save(update_fields=["value", "is_edited"])
            return self.scv

        # SCV editable-only field
        self.scv.is_edited = is_edited

        if is_edited:
            casted = self._cast_raw_value(new_raw_value)
            self.scv.value = str(
                self._apply_display_constraints(
                    self.column, casted, self.holding
                )
            )
        else:
            self.refresh_display_value()

        self.scv.save(update_fields=["value", "is_edited"])

        self._trigger_formula_updates()

        return self.scv

    # ============================================================
    # RAW CASTING (NO ROUNDING)
    # ============================================================
    def _cast_raw_value(self, raw_value):
        if raw_value in [None, ""]:
            return None

        dt = self.column.data_type
        if dt == "decimal":
            return Decimal(str(raw_value))
        if dt == "integer":
            return int(raw_value)
        if dt == "string":
            return str(raw_value)
        return raw_value

    # ============================================================
    # STATIC DEFAULT VALUES
    # ============================================================
    @staticmethod
    def _static_default(column):
        if column.data_type == "decimal":
            dp = SchemaColumnValueManager._decimal_places_for_column(
                column, None
            )
            return str(Decimal("0").scaleb(-dp))

        if column.data_type == "string":
            return "-"

        if column.data_type == "integer":
            return "0"

        return None

    # ============================================================
    # FIELD RESOLUTION (supports "crypto_detail__base_symbol")
    # ============================================================
    @staticmethod
    def _resolve_path(obj, path):
        parts = path.split("__")
        for part in parts:
            obj = getattr(obj, part, None)
            if obj is None:
                return None
        return obj
