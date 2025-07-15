"""
users.serializers.auth
~~~~~~~~~~~~~~~~~~~~~~
Contains serializers for authentication and signup logic.
"""

from datetime import date
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from users.models import User
from users.services import bootstrap_user_profile_and_portfolio


class UserCreateSerializer(BaseUserCreateSerializer):
    """
    Serializer for creating a user via Django's ORM.
    Typically used internally for user creation.
    """
    class Meta(BaseUserCreateSerializer.Meta):
        model = get_user_model()
        fields = ('id', 'email', 'first_name',
                  'last_name', 'birth_date', 'password')


class SignupSerializer(serializers.Serializer):
    """
    Handles user signup validation and creation.

    Responsibilities:
    - Validate email uniqueness
    - Validate password against Django's password policies
    - Ensure user is at least 13 years old
    - Create user and default Profile

    Fields:
        email, first_name, last_name, password, birth_date, country, preferred_currency
    """

    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    birth_date = serializers.DateField(required=True)

    # Only allow country and preferred_currency at signup
    country = serializers.CharField(required=False)
    preferred_currency = serializers.CharField(required=False)

    def validate_birth_date(self, value):
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 13:
            raise serializers.ValidationError("User must be at least 13 years old.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value):
        user = User(
            email=self.initial_data.get('email', ''),
            first_name=self.initial_data.get('first_name', ''),
            last_name=self.initial_data.get('last_name', '')
        )
        validate_password(value, user=user)
        return value

    def create(self, validated_data):
        country = validated_data.pop('country', 'US')
        preferred_currency = validated_data.pop('preferred_currency', 'USD')

        user = User.objects.create_user(**validated_data)

        profile = bootstrap_user_profile_and_portfolio(user, country, preferred_currency)

        # Set language from Accept-Language header
        profile.language = self.context.get('request').META.get(
            'HTTP_ACCEPT_LANGUAGE', 'en'
        ).split(',')[0].split('-')[0].lower() or 'en'
        profile.save(update_fields=["language"])

        return user
