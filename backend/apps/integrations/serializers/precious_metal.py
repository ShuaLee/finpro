from rest_framework import serializers


class PreciousMetalListingSerializer(serializers.Serializer):
    metal = serializers.CharField()
    name = serializers.CharField()
    spot_symbol = serializers.CharField()
    spot_name = serializers.CharField()
    currency = serializers.CharField()
