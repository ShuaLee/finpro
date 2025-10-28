from schemas.models.constraints import MasterConstraint, SchemaConstraint


class SchemaConstraintManager:
    @staticmethod
    def create_from_master(column, field_def=None):
        """
        Create SchemaConstraints for the given SchemaColumn
        based on MasterConstraints for its data_type.
        Optionally applies field-specific overrides.
        """
        # Fetch all master constraints for this column's data type
        masters = MasterConstraint.objects.filter(
            applies_to=column.data_type, is_active=True
        )

        # Gather any overrides from SchemaFieldDefinition if present
        overrides = {}
        if field_def and hasattr(field_def, "constraint_overrides"):
            overrides = field_def.constraint_overrides or {}

        # Create constraint instances for each applicable rule
        for master in masters:
            value = overrides.get(master.name, master.default_value)

            SchemaConstraint.objects.get_or_create(
                column=column,
                name=master.name,
                defaults={
                    "label": master.label,
                    "applies_to": master.applies_to,
                    "value": value,
                    "min_limit": master.min_limit,
                    "max_limit": master.max_limit,
                    "is_editable": master.is_editable,
                },
            )
