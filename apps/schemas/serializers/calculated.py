from rest_framework import serializers
from schemas.models import SchemaColumn
import re


class AddCalculatedColumnSerializer(serializers.Serializer):
    title = serializers.CharField()
    formula = serializers.CharField()

    def validate_formula(self, formula):
        # Allow safe characters only
        allowed_pattern = r'^[\w\s\+\-\*/\.\(\)]+$'
        if not re.match(allowed_pattern, formula):
            raise serializers.ValidationError("Invalid characters in formula.")
        
        # Extract variable names
        variables = re.findall(r'[a-zA-Z_]\w*', formula)
        if not variables:
            raise serializers.ValidationError("Formula must include at least one variable.")
        
        return formula
    
    def validate(self, data):
        schema = self.context.get("schema")
        if not schema:
            raise serializers.ValidationError("Schema is required in context.")
        
        formula = data["formula"]
        variables = re.findall(r'[a-zA-Z_]\w*', formula)

        existing = [
            col.source_field.lower()
            for col in schema.columns.all()
            if col.source_field
        ]

        missing = [v for v in variables if v.lower() not in existing]

        data["missing_variables"] = missing
        return data
