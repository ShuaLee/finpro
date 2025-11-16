from decimal import Decimal, ROUND_HALF_UP


class SchemaColumnValueManager:
    def __init__(self, scv):
        # Lazy import to avoid circulars
        from schemas.models.schema import SchemaColumnValue

        if not isinstance(scv, SchemaColumnValue):
            raise TypeError("Expected a SchemaColumnValue instance")
        self.scv = scv
        self.column = scv.column
        self.holding = scv.holding

    # -----------------------------
    # Core lifecycle methods
    # -----------------------------
    @classmethod
    def ensure_for_holding(cls, holding):
        """Create SCVs for all columns in the holding’s active schema."""
        from schemas.models.schema import SchemaColumnValue

        schema = holding.active_schema
        if not schema:
            return

        for column in schema.columns.all():
            cls.get_or_create(holding, column)

    @classmethod
    def ensure_for_column(cls, column):
        """Create SCVs for all holdings when a new column is added."""
        from schemas.models.schema import SchemaColumnValue

        schema = column.schema
        # Only apply to accounts with this schema's account_type in this portfolio
        for account in schema.portfolio.accounts.filter(account_type=schema.account_type):
            for holding in account.holdings.all():
                cls.get_or_create(holding, column)

    @classmethod
    def refresh_for_holding(cls, holding):
        """Refresh all SCVs for a given holding."""
        schema = holding.active_schema
        if not schema:
            return

        for column in schema.columns.all():
            manager = cls.get_or_create(holding, column)
            manager.apply_rules()
            manager.scv.save()

    @classmethod
    def get_or_create(cls, holding, column):
        from schemas.models.schema import SchemaColumnValue

        scv, created = SchemaColumnValue.objects.get_or_create(
            column=column,
            holding=holding,
            defaults={
                "value": cls.default_for_column(column, holding),
                "is_edited": False,
            },
        )
        return cls(scv)

    # -----------------------------
    # Value resolution
    # -----------------------------
    def save_value(self, raw_value, is_edited: bool):
        if self.column.source == "holding":
            casted = self._cast_value(raw_value)
            self._validate_against_constraints(casted)
            setattr(self.holding, self.column.source_field, casted)
            self.holding.save(update_fields=[self.column.source_field])

            self.scv.value = str(casted)
            self.scv.is_edited = False
            return self.scv

        self.scv.is_edited = is_edited
        if is_edited:
            casted = self._cast_value(raw_value)
            self._validate_against_constraints(casted)
            self.scv.value = str(casted)
        else:
            self.reset_to_source()

        return self.scv

    def reset_to_source(self):
        self.scv.is_edited = False
        self.scv.value = self.resolve()
        return self.scv

    def resolve(self):
        if self.column.formula:
            # TODO: add formula evaluation
            return None

        if self.column.source_field:
            if hasattr(self.holding, self.column.source_field):
                return getattr(self.holding, self.column.source_field, None)

            if hasattr(self.holding, "asset"):
                asset = self.holding.asset
                if asset and hasattr(asset, self.column.source_field):
                    return getattr(asset, self.column.source_field, None)

        return self._static_default(self.column)

    def _cast_value(self, raw_value):
        if raw_value in [None, ""]:
            return None
        dt = self.column.data_type
        if dt == "decimal":
            dp = self._decimal_places()
            q = Decimal("1." + "0" * dp)
            return Decimal(str(raw_value)).quantize(q)
        if dt == "integer":
            return int(raw_value)
        if dt == "string":
            return str(raw_value)
        return raw_value

    @staticmethod
    def default_for_column(column, holding):
        value = None
        if column.source == "holding" and column.source_field:
            value = getattr(holding, column.source_field, None)
        elif column.source == "asset" and column.source_field:
            asset = getattr(holding, "asset", None)
            if asset:
                value = getattr(asset, column.source_field, None)
        if value is None:
            value = SchemaColumnValueManager._static_default(column)
        return value

    @staticmethod
    def _static_default(column):
        if column.data_type == "decimal":
            c = column.constraints_set.filter(name="decimal_places").first()
            dp = int(c.value or c.default_value or 2) if c else 2
            return str(Decimal("0").quantize(Decimal(f"1.{'0'*dp}")))
        elif column.data_type == "string":
            return "-"
        elif column.data_type == "integer":
            return "0"
        return None

    def apply_rules(self):
        if self.column.source == "holding":
            self.save_value(self.scv.value, is_edited=False)
        elif self.scv.is_edited:
            self.save_value(self.scv.value, is_edited=True)
        else:
            self.reset_to_source()

    def _decimal_places(self):
        """Helper to get decimal_places constraint value."""
        c = self.column.constraints_set.filter(name="decimal_places").first()
        return int(c.value or c.default_value or 2) if c else 2

    def _validate_against_constraints(self, value):
        """
        Validate and normalize (round) a holding/SCV value according to schema constraints.
        Decimal places → auto-quantized
        Min/max → raise errors
        """
        constraints = self.column.constraints_set.all()

        # Prepare numeric form safely
        is_numeric = False
        numeric = None

        if value is not None:
            try:
                numeric = Decimal(str(value))
                is_numeric = True
            except:
                is_numeric = False

        for c in constraints:

            # Skip empty/disabled constraints
            if c.value in [None, "", "-", "None"]:
                continue

            # -----------------------------
            # NUMERIC CONSTRAINTS
            # -----------------------------
            if is_numeric and c.applies_to in ("decimal", "integer"):

                # 1. MINIMUM VALUE (error)
                if c.name == "min_value":
                    limit = Decimal(str(c.value))
                    if numeric < limit:
                        raise ValueError(
                            f"{self.column.title}: value {numeric} is below minimum {limit}"
                        )

                # 2. MAXIMUM VALUE (error)
                if c.name == "max_value":
                    limit = Decimal(str(c.value))
                    if numeric > limit:
                        raise ValueError(
                            f"{self.column.title}: value {numeric} exceeds maximum {limit}"
                        )

                # 3. DECIMAL PLACES (auto-round)
                if c.name == "decimal_places":
                    allowed_dp = int(c.value)
                    quantizer = Decimal("1").scaleb(-allowed_dp)
                    numeric = numeric.quantize(
                        quantizer, rounding=ROUND_HALF_UP)
                    value = numeric  # return this updated value

            # -----------------------------
            # STRING CONSTRAINTS
            # -----------------------------
            if c.applies_to == "string" and isinstance(value, str):
                if c.name == "max_length":
                    if len(value) > int(c.value):
                        raise ValueError(
                            f"{self.column.title}: string exceeds max length {c.value}"
                        )

        return value  # VERY IMPORTANT: return rounded/normalized value
