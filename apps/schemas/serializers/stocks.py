from rest_framework import serializers
from schemas.models.stocks import StockPortfolioSCV
from schemas.services import recalculate_calculated_columns


class StockPortfolioSCVEditSerializer(serializers.ModelSerializer):
    value = serializers.CharField(allow_null=True, required=False)

    class Meta:
        model = StockPortfolioSCV
        fields = ['id', 'value', 'is_edited']

    def validate(self, data):
        value = data.get('value')
        column = self.instance.column

        # Prevent editing calculated columns
        if column.source == 'calculated':
            raise serializers.ValidationError(
                "Calculated columns cannot be edited.")

        # Check if column is editable
        if not column.editable:
            raise serializers.ValidationError("This column is not editable.")

        # Validate type if value provided
        if value not in [None, '']:
            try:
                if column.data_type == 'decimal':
                    float(value)
                elif column.data_type == 'integer':
                    int(value)
                elif column.data_type == 'string':
                    str(value)
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'value': f"Invalid input for type '{column.data_type}'."
                })

        return data

    def update(self, instance, validated_data):
        value = validated_data.get('value')

        # Reset override if blank or None
        if value in [None, '']:
            instance.value = None
            instance.is_edited = False
        else:
            instance.value = value
            instance.is_edited = True

        instance.save()

        # ✅ Trigger recalculation for dependent calculated columns
        schema = instance.column.schema
        holding = instance.holding
        recalculate_calculated_columns(schema, holding)

        return instance
