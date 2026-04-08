from rest_framework import serializers

from apps.integrations.models import ActiveCryptoListing


class ActiveCryptoListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActiveCryptoListing
        fields = ["symbol", "name", "base_symbol", "quote_currency"]
        read_only_fields = fields
