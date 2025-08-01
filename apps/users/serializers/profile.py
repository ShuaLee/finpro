"""
users.serializers.profile
~~~~~~~~~~~~~~~~~~~~~~~~~~
Serializer for reading and updating Profile data, including subscription plans.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from common.utils.country_currency_catalog import (
    validate_country_code,
    validate_currency_code,
)
from users.models import Profile
from subscriptions.models import AccountType, Plan


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for reading and updating Profile data.

    Features:
    - Prevent clearing required fields once profile is complete.
    - Automatically mark profile as complete when required fields are set.
    - Includes is_profile_complete in the response for frontend logic.
    """

    email = serializers.SerializerMethodField()
    is_profile_complete = serializers.BooleanField(
        read_only=True)  # ✅ Add this
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
            'receive_email_updates', 'created_at', 'is_profile_complete'
        ]
        read_only_fields = ['id', 'email', 'created_at', 'is_profile_complete']

    def get_email(self, obj):
        """Return user's email for profile representation."""
        return obj.user.email

    def validate_country(self, value):
        value = value.upper()
        try:
            validate_country_code(value)
        except (DjangoValidationError, ValueError) as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate_preferred_currency(self, value):
        value = value.upper()
        try:
            validate_currency_code(value)
        except (DjangoValidationError, ValueError) as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate(self, attrs):
        """
        Prevent clearing required fields after profile completion.
        """
        profile = self.instance
        if profile and profile.is_profile_complete:
            for field in ['full_name', 'country', 'preferred_currency']:
                if field in attrs and not attrs[field]:
                    raise serializers.ValidationError({
                        field: f"You cannot clear {field} after profile completion."
                    })
        return attrs

    def update(self, instance, validated_data):
        """
        Update profile fields, normalize codes, and set is_profile_complete if all required fields exist.
        """
        # Normalize country and currency if provided
        if 'country' in validated_data and validated_data['country']:
            validated_data['country'] = validated_data['country'].upper()
        if 'preferred_currency' in validated_data and validated_data['preferred_currency']:
            validated_data['preferred_currency'] = validated_data['preferred_currency'].upper(
            )

        # Apply updates
        for field, value in validated_data.items():
            setattr(instance, field, value)

        # Check if profile can now be marked complete
        if not instance.is_profile_complete:
            required_fields = ['full_name', 'country', 'preferred_currency']
            if all(getattr(instance, f) for f in required_fields):
                instance.is_profile_complete = True

        instance.save()
        return instance


class CompleteProfileSerializer(serializers.ModelSerializer):
    """
    Serializer used exclusively for completing a user profile after signup.
    Requires: full_name, country, preferred_currency.
    """

    class Meta:
        model = Profile
        fields = ['full_name', 'country', 'preferred_currency']

    def validate_country(self, value):
        value = value.upper()
        try:
            validate_country_code(value)
        except (DjangoValidationError, ValueError) as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate_preferred_currency(self, value):
        value = value.upper()
        try:
            validate_currency_code(value)
        except (DjangoValidationError, ValueError) as e:
            raise serializers.ValidationError(str(e))
        return value

    def update(self, instance, validated_data):
        instance.full_name = validated_data.get(
            "full_name", instance.full_name)
        instance.country = validated_data.get(
            "country", instance.country).upper()
        instance.preferred_currency = validated_data.get(
            "preferred_currency", instance.preferred_currency).upper()

        # Set as complete
        instance.is_profile_complete = True
        instance.save()
        return instance
