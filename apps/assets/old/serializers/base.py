from rest_framework import serializers
from assets.models.base import HoldingThemeValue


class HoldingThemeValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = HoldingThemeValue
        fields = ['id', 'theme', 'value_string',
                  'value_decimal', 'value_integer']
