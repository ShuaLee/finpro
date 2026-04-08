from rest_framework import serializers

from apps.integrations.models import ActiveCommodityListing


class ActiveCommodityListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActiveCommodityListing
        fields = ["symbol", "name", "exchange", "trade_month", "currency"]
        read_only_fields = fields
