from fx.models.fx import FXCurrency


class SchemaConstraintEnumResolver:
    """
    Resolves enum constraints for SchemaColumns.

    Driven entirely by constraint values,
    NOT column identifiers.
    """

    @staticmethod
    def resolve(constraint, *, column=None, holding=None):
        if constraint.name != "enum":
            return []

        enum_key = constraint.value_string

        if enum_key == "fx_currency":
            return list(
                FXCurrency.objects
                .order_by("code")
                .values_list("code", flat=True)
            )

        return []
