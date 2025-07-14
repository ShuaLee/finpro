from rest_framework import serializers
from ..models.stocks import StockPortfolioSCV


class StockPortfolioSCVEditSerializer(serializers.ModelSerializer):
    value = serializers.CharField(allow_null=True, required=False)

    class Meta:
        model = StockPortfolioSCV
        fields = ['id', 'value', 'is_edited']

    def validate(self, data):
        value = data.get('value')
        column = self.instance.column

        if not column.editable:
            raise serializers.ValidationError("This column is not editable.")

        data_type = column.data_type

        if value is not None:
            try:
                if data_type == 'decimal':
                    float(value)
                elif data_type == 'integer':
                    int(value)
                elif data_type == 'string':
                    str(value)
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'value': f"Invalid input for type '{data_type}'"
                })

        return data

    def update(self, instance, validated_data):
        value = validated_data.get('value')

        instance.value = value
        instance.is_edited = True
        instance.save()

        return instance
