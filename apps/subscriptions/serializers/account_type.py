from rest_framework import serializers
from subscriptions.models import AccountType


class AccountTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for AccountType model.
    Provides basic fields for reading and (optionally) writing.
    """

    class Meta:
        model = AccountType
        fields = ['id', 'name', 'slug', 'description']
        read_only_fields = ['id']
