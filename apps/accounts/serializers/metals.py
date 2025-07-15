from rest_framework import serializers
from accounts.models import StorageFacility

class StorageFacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageFacility
        fields = ['id', 'name', 'is_lending_account', 'is_insured', 'interest_rate', 'created_at']
        read_only_fields = ['id', 'created_at']


class StorageFacilityCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageFacility
        fields = ['name', 'is_lending_account', 'is_insured', 'interest_rate']