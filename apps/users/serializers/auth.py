"""
users.serializers.auth
~~~~~~~~~~~~~~~~~~~~~~
Contains serializers for authentication and signup logic.
"""

from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from users.models import User
from users.services import bootstrap_user_profile


class UserCreateSerializer(BaseUserCreateSerializer):
    """
    Serializer for creating a user via Django's ORM.
    Typically used internally for user creation.
    """
    class Meta(BaseUserCreateSerializer.Meta):
        model = get_user_model()
        fields = ('id', 'email', 'password')


class SignupSerializer(serializers.Serializer):
    """
    Handles user signup validation and creation.

    Responsibilities:
    - Validate email uniqueness
    - Validate password against Django's password policies
    - Confirm user is over 13 years old (checkbox)
    - Create user and default Profile

    Fields:
        email, first_name, last_name (optional), password, is_over_13,
        country (optional), preferred_currency (optional)
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    is_over_13 = serializers.BooleanField()

    # Optional profile fields
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    country = serializers.CharField(required=False)
    preferred_currency = serializers.CharField(required=False)

    def validate_is_over_13(self, value):
        if value is not True:
            raise serializers.ValidationError("You must confirm you are at least 13 years old.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value):
        user = User(
            email=self.initial_data.get('email', ''),
        )
        validate_password(value, user=user)
        return value

    def create(self, validated_data):
        # Extract profile-related fields (if provided)
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        country = validated_data.pop('country', 'US')
        preferred_currency = validated_data.pop('preferred_currency', 'USD')

        # Create user
        user = User.objects.create_user(**validated_data)

        # Create profile with optional data
        profile = bootstrap_user_profile(user)
        if first_name:
            profile.first_name = first_name
        if last_name:
            profile.last_name = last_name
        if country:
            profile.country = country
        if preferred_currency:
            profile.preferred_currency = preferred_currency

        # Set language from Accept-Language header (fallback: 'en')
        profile.language = self.context.get('request').META.get(
            'HTTP_ACCEPT_LANGUAGE', 'en'
        ).split(',')[0].split('-')[0].lower() or 'en'
        profile.save(update_fields=["language"])

        return user
