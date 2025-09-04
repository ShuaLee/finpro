from schemas.validators import validate_constraints


class SchemaTemplateManager:
    """
    Handles the creation and retrieval of schema column templates.
    """

    @staticmethod
    def schema_field(
        title: str,
        data_type: str,
        source_field: str = None,
        is_editable: bool = True,
        is_deletable: bool = True,
        is_default: bool = False,
        is_system: bool = True,
        constraints: dict = None,
        source: str = None,
        formula_key: str = None,
        display_order: int = None,
    ) -> dict:
        """
        Factory for schema field definitions.
        - If is_default=True → display_order must be provided.
        - If is_default=False → display_order is ignored (set to None).
        """

        if constraints is None:
            constraints = {}

        # 🔒 Validate constraints
        validate_constraints(data_type, constraints)

        if is_default and display_order is None:
            raise ValueError(
                f"Default column '{title}' must define an explicit display_order."
            )

        return {
            "title": title,
            "data_type": data_type,
            "source_field": source_field,
            "is_editable": is_editable,
            "is_deletable": is_deletable,
            "is_default": is_default,
            "is_system": is_system,
            "constraints": constraints,
            "source": source,
            "formula_key": formula_key,
            "display_order": display_order if is_default else None,
        }

    # @staticmethod
    # def get_defaults(schema_type: str, account_model_class=None):
    #     """
    #     Returns default column definitions from registry for a given schema_type.
    #     """
    #     from schemas.config import SCHEMA_CONFIG_REGISTRY

    #     config = SCHEMA_CONFIG_REGISTRY.get(schema_type)
    #     if not config:
    #         raise ValueError(
    #             f"No schema config found for schema type '{schema_type}'")

    #     # If nested per account model
    #     if isinstance(config, dict) and account_model_class:
    #         config = config.get(account_model_class)
    #         if not config:
    #             raise ValueError(
    #                 f"No config found for schema_type '{schema_type}' and model '{account_model_class.__name__}'"
    #             )

    #     columns, display_counter = [], 1
    #     for source, fields in config.items():
    #         for source_field, meta in fields.items():
    #             if meta.get("is_default", False):
    #                 columns.append({
    #                     "source": source,
    #                     "source_field": source_field,
    #                     "title": meta["title"],
    #                     "data_type": meta["data_type"],
    #                     "is_editable": meta.get("is_editable", True),
    #                     "is_deletable": meta.get("is_deletable", True),
    #                     "is_system": meta.get("is_system", False),
    #                     "formula_key": meta.get("formula_key"),
    #                     "constraints": meta.get("constraints", {}),
    #                     "display_order": meta.get("display_order") or display_counter,
    #                 })
    #                 display_counter += 1

    #     return columns
