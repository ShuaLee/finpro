"""
users.serializers.profile
~~~~~~~~~~~~~~~~~~~~~~~~~~
Serializer for reading and updating Profile data, including subscription plans.
"""
from django.core.exceptions import ValidationError
from rest_framework import serializers
from common.utils.country_data import validate_currency_code, validate_country_code
from users.models import Profile
from subscriptions.models import AccountType, Plan


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
    plan = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Plan.objects.filter(is_active=True),
        required=False
    )
    account_type = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=AccountType.objects.all(),
        required=False
    )

    class Meta:
        model = Profile
        fields = [
            'id', 'email', 'full_name', 'account_type', 'plan',
            'language', 'country', 'preferred_currency', 'birth_date',
            'receive_email_updates', 'created_at'
        ]
        read_only_fields = ['id', 'email', 'created_at']

    def get_email(self, obj):
        """Return user's email for profile representation."""
        return obj.user.email

    def validate_preferred_currency(self, value):
        """
        Validate currency code against ISO 4217 codes from pycountry.
        Normalize to uppercase.
        """
        value = value.upper()
        try:
            validate_currency_code(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate_country(self, value):
        """
        Validate country code against ISO 3166-1 alpha-2.
        Normalize to uppercase.
        """
        value = value.upper()
        try:
            validate_country_code(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def update(self, instance, validated_data):
        """
        Update allowed fields in the Profile model.
        """
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance
