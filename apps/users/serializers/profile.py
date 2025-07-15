"""
users.serializers.profile
~~~~~~~~~~~~~~~~~~~~~~~~~~
Contains serializers for managing user profiles.
"""

from django.conf import settings
from rest_framework import serializers
from users.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for reading and updating Profile data.

    Fields:
        email (from related user), account_type, plan, language, country,
        preferred_currency, birth_date, is_asset_manager, receive_email_updates
    """
    email = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id', 'email', 'account_type', 'plan', 'language', 'country', 'preferred_currency',
            'birth_date', 'is_asset_manager', 'receive_email_updates', 'created_at'
        ]
        read_only_fields = ['id', 'email', 'created_at']

    def get_email(self, obj):
        """
        Return user's email for profile representation.
        """
        return obj.user.email

    def validate_preferred_currency(self, value):
        """
        Ensure currency is valid ISO code based on system settings.
        """
        valid_codes = [code for code, name in settings.CURRENCY_CHOICES]
        if value not in valid_codes:
            raise serializers.ValidationError(
                "Invalid currency code. Must be a valid ISO 4217 code (e.g., USD, EUR, AUD)."
            )
        return value

    def update(self, instance, validated_data):
        """
        Update allowed fields in the Profile model.
        """
        allowed_fields = [
            'account_type', 'plan', 'language', 'country',
            'preferred_currency', 'birth_date', 'is_asset_manager', 'receive_email_updates'
        ]
        for field in allowed_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance