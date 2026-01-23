from rest_framework import serializers
from assets.models.base import InvestmentTheme


class AddCustomColumnSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=100)
    data_type = serializers.ChoiceField(choices=[
        ('decimal', 'Decimal'),
        ('integer', 'Integer'),
        ('string', 'Text'),
        ('date', 'Date'),
        ('url', 'URL'),
    ])
    decimal_places = serializers.IntegerField(required=False)
    investment_theme_id = serializers.IntegerField(
        required=False, allow_null=True)

    def validate_investment_theme_id(self, value):
        if value is None:
            return None
        user = self.context["request"].user
        try:
            theme = InvestmentTheme.objects.get(
                id=value, portfolio__profile__user=user)
        except InvestmentTheme.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid theme for your portfolio.")
        return theme
