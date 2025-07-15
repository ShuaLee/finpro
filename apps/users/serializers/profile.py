"""
users.serializers.profile
~~~~~~~~~~~~~~~~~~~~~~~~~~
Contains serializers for managing user profiles.
"""

from django.conf import settings
from rest_framework import serializers
from ..models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for reading and updating Profile data.

    Fields:
        email (from related user), currency, language, created_at, theme, receive_email_updates
    """
    email = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id', 'account_type', 'plan', 'language', 'country', 'preferred_currency',
            'theme', 'is_asset_manager', 'receive_email_updates', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_email(self, obj):
        """
        Return user's email for profile representation.
        """
        return obj.user.email

    def validate_currency(self, value):
        """
        Ensure currency is valid ISO code based on system settings.
        """
        valid_codes = [code for code, name in settings.CURRENCY_CHOICES]
        if value not in valid_codes:
            raise serializers.ValidationError(
                f"Invalid currency code. Must be a valid ISO 4217 code (e.g., USD, EUR, AUD).")
        return value

    def update(self, instance, validated_data):
        """
        Update only allowed fields in the Profile model.
        """
        for field in ['currency', 'language', 'theme', 'receive_email_updates']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance
