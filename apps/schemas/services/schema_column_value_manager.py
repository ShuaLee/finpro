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
        """
        Every holding for accounts of this schema must get an SCV for this column.
        """

        schema = column.schema
        accounts = schema.portfolio.accounts.filter(
            account_type=schema.account_type)

        for account in accounts:
            for holding in account.holdings.all():
                cls.get_or_create(holding, column)

    @classmethod
    def refresh_for_holding(cls, holding):
        schema = holding.active_schema
        if not schema:
            return

        for column in schema.columns.all():
            manager = cls.get_or_create(holding, column)
            manager.refresh_display_value()
            manager.scv.save(update_fields=["value", "is_edited"])

    @classmethod
    def get_or_create(cls, holding, column):
        from schemas.models.schema import SchemaColumnValue

        # Compute initial display value from holding/raw
        initial_value = cls.display_for_column(column, holding)

        scv, created = SchemaColumnValue.objects.get_or_create(
            column=column,
            holding=holding,
            defaults={
                "value": initial_value,
                "is_edited": False,
            },
        )
        return cls(scv)

    # ============================================================
    # SCV DISPLAY LOGIC
    # ============================================================
    @staticmethod
    def display_for_column(column, holding):
        """Compute the display value for a column using SCHEMA constraints."""

        raw_value = None

        # Resolve raw value from holding/asset
        if column.source == "holding" and column.source_field:
            raw_value = getattr(holding, column.source_field, None)
        elif column.source == "asset" and column.source_field:
            asset = getattr(holding, "asset", None)
            if asset:
                raw_value = getattr(asset, column.source_field, None)

        # Static default (0.00, "-", etc.)
        if raw_value is None:
            return SchemaColumnValueManager._static_default(column)

        # Format using constraints (decimal_places, max_length, etc.)
        return SchemaColumnValueManager._apply_display_constraints(
            column, raw_value
        )

    def refresh_display_value(self):
        """Recompute SCV value from raw holding value + schema constraints"""
        self.scv.value = self.display_for_column(self.column, self.holding)
        self.scv.is_edited = False

    # ============================================================
    # APPLY CONSTRAINTS (DISPLAY ONLY)
    # ============================================================
    @staticmethod
    def _apply_display_constraints(column, raw_value):
        """
        Applies SCHEMA constraints to raw value **for display only**.
        Does NOT change the raw value stored on Holding.
        """

        dt = column.data_type

        # -------------------------
        # DECIMAL DISPLAY
        # -------------------------
        if dt == "decimal":
            try:
                numeric = Decimal(str(raw_value))
            except:
                return raw_value

            dp = SchemaColumnValueManager._decimal_places_for_column(column)
            quant = Decimal("1").scaleb(-dp)

            return str(numeric.quantize(quant, rounding=ROUND_HALF_UP))

        # -------------------------
        # STRING DISPLAY
        # -------------------------
        if dt == "string":
            try:
                s = str(raw_value)
            except:
                return raw_value

            max_len = SchemaColumnValueManager._max_length_for_column(column)
            return s[:max_len] if max_len and len(s) > max_len else s

        # -------------------------
        # INTEGER DISPLAY
        # -------------------------
        if dt == "integer":
            try:
                return str(int(raw_value))
            except:
                return raw_value

        return raw_value

    @staticmethod
    def _decimal_places_for_column(column):
        c = column.constraints_set.filter(name="decimal_places").first()
        return int(c.value or c.default_value or 2) if c else 2

    @staticmethod
    def _max_length_for_column(column):
        c = column.constraints_set.filter(name="max_length").first()
        return int(c.value or c.default_value or 255) if c else None

    # ============================================================
    # EDITING VALUES (user manually edits SCV)
    # ============================================================
    def save_value(self, new_raw_value, is_edited: bool):
        """
        Saving SCV:
          - If editable and user edits value: apply constraints, store in SCV
          - If based on holding source: write raw_value directly to holding
        """

        # -------------------------
        # HOLDING-SOURCE COLUMN
        # -------------------------
        if self.column.source == "holding":
            casted = self._cast_raw_value(new_raw_value)
            setattr(self.holding, self.column.source_field, casted)
            self.holding.save(update_fields=[self.column.source_field])

            # SCV mirrors the new display value
            self.refresh_display_value()
            self.scv.save(update_fields=["value", "is_edited"])
            return self.scv

        # -------------------------
        # EDITABLE SCV (no holding field)
        # -------------------------
        self.scv.is_edited = is_edited

        if is_edited:
            casted = self._cast_raw_value(new_raw_value)
            self.scv.value = str(
                self._apply_display_constraints(self.column, casted)
            )
        else:
            # Reset to auto-format-from-holding
            self.refresh_display_value()

        self.scv.save(update_fields=["value", "is_edited"])
        return self.scv

    # ============================================================
    # CAST RAW VALUE (no rounding!)
    # ============================================================
    def _cast_raw_value(self, raw_value):
        """
        Convert user raw input to proper Python type.
        ❗ DO NOT ROUND HERE — raw values must remain intact.
        """
        if raw_value in [None, ""]:
            return None

        dt = self.column.data_type
        if dt == "decimal":
            return Decimal(str(raw_value))   # NO quantize here
        if dt == "integer":
            return int(raw_value)
        if dt == "string":
            return str(raw_value)

        return raw_value

    # ============================================================
    # STATIC DEFAULTS
    # ============================================================
    @staticmethod
    def _static_default(column):
        if column.data_type == "decimal":
            dp = SchemaColumnValueManager._decimal_places_for_column(column)
            return str(Decimal("0").scaleb(-dp))
        if column.data_type == "string":
            return "-"
        if column.data_type == "integer":
            return "0"
        return None
