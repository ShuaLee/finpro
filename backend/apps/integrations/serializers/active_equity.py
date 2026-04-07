from rest_framework import serializers

from apps.integrations.models import ActiveEquityListing


class ActiveEquityListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActiveEquityListing
        fields = ["symbol", "name"]
        read_only_fields = fields
