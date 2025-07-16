"""
users.serializers.profile
~~~~~~~~~~~~~~~~~~~~~~~~~~
Serializer for reading and updating Profile data, including subscription plans.
"""

from rest_framework import serializers
from django.conf import settings
from users.models import Profile
from subscriptions.models import Plan


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for reading and updating Profile data.

    Fields:
        - id: Primary key (read-only)
        - email: Derived from related user model (read-only)
        - account_type: Individual or Manager
        - plan: Represented by slug for readability; allows updates by slug
        - language: Preferred language
        - country: ISO country code
        - preferred_currency: ISO currency code
        - birth_date: Optional DOB
        - is_asset_manager: Boolean flag
        - receive_email_updates: Marketing email preference
        - created_at: Profile creation timestamp (read-only)

    Notes:
        - Plan updates only accept active plan slugs.
        - Currency validation uses ISO codes via settings.
    """

    email = serializers.SerializerMethodField()
    # ✅ Allow updating plan by slug (was read-only before)
    plan = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Plan.objects.filter(is_active=True),
        required=False
    )

    class Meta:
        model = Profile
        fields = [
            'id', 'email', 'account_type', 'plan', 'language', 'country',
            'preferred_currency', 'birth_date', 'is_asset_manager',
            'receive_email_updates', 'created_at'
        ]
        read_only_fields = ['id', 'email', 'created_at']

    def get_email(self, obj):
        """Return user's email for profile representation."""
        return obj.user.email

    def validate_preferred_currency(self, value):
        """
        Ensure currency is a valid ISO code based on system settings.
        """
        valid_codes = [code for code, name in settings.CURRENCY_CHOICES]
        if value not in valid_codes:
            raise serializers.ValidationError(
                "Invalid currency code. Must be a valid ISO 4217 code (e.g., USD, EUR, AUD)."
            )
        return value

    def update(self, instance, validated_data):
        """
        Update allowed fields in the Profile model, including plan changes.
        """
        allowed_fields = [
            'account_type', 'plan', 'language', 'country',
            'preferred_currency', 'birth_date', 'is_asset_manager',
            'receive_email_updates'
        ]
        for field in allowed_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance
