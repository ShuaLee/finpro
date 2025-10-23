class SchemaConstraintManager:
    @staticmethod
    def create_from_master(column):
        """
        Duplicate all applicable MasterConstraints for a given SchemaColumn.
        """
        from schemas.models.constraints import MasterConstraint, SchemaConstraint

        masters = MasterConstraint.objects.filter(
            applies_to=column.data_type, is_active=True
        )

        for master in masters:
            SchemaConstraint.objects.create(
                column=column,
                name=master.name,
                label=master.label,
                value=master.default_value,
                min_limit=master.min_limit,
                max_limit=master.max_limit,
                applies_to=master.applies_to,
                is_editable=master.is_editable,
            )
