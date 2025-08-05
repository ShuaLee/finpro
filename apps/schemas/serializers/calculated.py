from rest_framework import serializers


class AddCalculatedColumnSerializer(serializers.Serializer):
    title = serializers.CharField()
    formula = serializers.CharField()
