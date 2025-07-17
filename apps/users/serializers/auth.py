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
    Serializer for user creation (used internally by Djoser).
    """
    class Meta(BaseUserCreateSerializer.Meta):
        model = get_user_model()
        fields = ('id', 'email', 'password')


class SignupSerializer(serializers.Serializer):
    """
    Handles user signup validation and creation.

    Flow:
    - Validate email (must be unique)
    - Validate password (Django's validators)
    - Confirm age requirement
    - Create user and default profile
    """

    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True, style={'input_type': 'password'})
    is_over_13 = serializers.BooleanField()

    def validate_is_over_13(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must confirm you are at least 13 years old."
            )
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value

    def validate_password(self, value):
        # Use Django's password validators
        user = User(email=self.initial_data.get('email', ''))
        validate_password(value, user=user)
        return value

    def create(self, validated_data):
        # Remove non-User field
        validated_data.pop('is_over_13', None)

        # Create user
        user = User.objects.create_user(**validated_data)

        # Bootstrap user profile with defaults
        profile = bootstrap_user_profile(user)

        # Set language from request headers
        request = self.context.get('request')
        if request:
            lang = request.META.get('HTTP_ACCEPT_LANGUAGE', 'en')
            profile.language = lang.split(',')[0].split('-')[0].lower() or 'en'
            profile.save(update_fields=['language'])

        return user
