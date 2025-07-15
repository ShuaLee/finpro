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
from ..models import Profile


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
        email, first_name, last_name, password, birth_date
    """
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    password = serializers.CharField(
        write_only=True, style={'input_type': 'password'})
    birth_date = serializers.DateField(required=True)

    def validate_birth_date(self, value):
        """
        Ensure user is at least 13 years old.
        """
        today = date.today()
        age = today.year - value.year - \
            ((today.month, today.day) < (value.month, value.day))
        if age < 13:
            raise serializers.ValidationError(
                "User must be at least 13 years old.")
        return value

    def validate_email(self, value):
        """
        Ensure email is unique.
        """
        if get_user_model().objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists.")
        return value

    def validate_password(self, value):
        """
        Validate password using Django's built-in validators.
        """
        user = get_user_model()(
            email=self.initial_data.get('email', ''),
            first_name=self.initial_data.get('first_name', ''),
            last_name=self.initial_data.get('last_name', '')
        )
        try:
            validate_password(value, user=user)
        except serializers.ValidationError as e:
            # Re-raise the validation error with the messages
            raise serializers.ValidationError(e.messages)
        return value

    def create(self, validated_data):
        """
        Create user and initialize related Profile.
        """
        user_data = {
            'email': validated_data['email'],
            'first_name': validated_data['first_name'],
            'last_name': validated_data['last_name'],
            'password': validated_data['password'],
            'birth_date': validated_data['birth_date']
        }

        # Create user (this will also create a default Profile)
        user = get_user_model().objects.create_user(**user_data)

        # Update the existing Profile with signup data
        profile = Profile.objects.get(user=user)
        profile.language = self.context.get('request').META.get(
            'HTTP_ACCEPT_LANGUAGE', 'en').split(',')[0].split('-')[0].lower() or 'en'
        profile.save()

        return user
