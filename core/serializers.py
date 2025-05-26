from datetime import date
from djoser.serializers import UserSerializer as BaseUserSerializer, UserCreateSerializer as BaseUserCreateSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Profile
from zoneinfo import available_timezones


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = get_user_model()
        fields = ('id', 'email', 'first_name', 'last_name', 'password')

class SignupCompleteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    birth_date = serializers.DateField()
    currency = serializers.CharField(max_length=10)
    language = serializers.CharField(max_length=30, default="en")

    def validate_birth_date(self, value):
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 13:
            raise serializers.ValidationError("User must be at least 13 years old.")
        return value

    def validate_language(self, value):
        # Simplify to ISO 639-1 (e.g., "en", "fr")
        if "-" in value:
            value = value.split("-")[0]
        # Add more validation if needed (e.g., list of supported languages)
        return value

    def validate_currency(self, value):
        # Optional: Validate against ISO 4217 codes (e.g., "USD", "EUR")
        valid_currencies = ["USD", "EUR", "GBP", "JPY"]  # Example list
        if value not in valid_currencies:
            raise serializers.ValidationError("Invalid currency code.")
        return value

    def create(self, validated_data):
        user_data = {
            'email': validated_data['email'],
            'first_name': validated_data['first_name'],
            'last_name': validated_data['last_name'],
            'password': validated_data['password']
        }
        profile_data = {
            'birth_date': validated_data['birth_date'],
            'currency': validated_data['currency'],
            'language': validated_data['language'],
            'profile_setup_complete': True
        }
        user = get_user_model().objects.create_user(**user_data)
        Profile.objects.create(user=user, **profile_data)
        return user


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = ['id', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'email', 'currency', 'language', 'birth_date',
            'is_asset_manager', 'profile_setup_complete', 'created_at',
            'receive_email_updates', 'theme'
        ]
        read_only_fields = ['user', 'is_asset_manager', 'profile_setup_complete', 'created_at']

    def get_email(self, obj):
        return obj.user.email

    def validate_birth_date(self, value):
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 13:
            raise serializers.ValidationError("User must be at least 13 years old.")
        return value

    def validate_currency(self, value):
        valid_currencies = ["USD", "EUR", "GBP", "JPY"]  # Example
        if value not in valid_currencies:
            raise serializers.ValidationError("Invalid currency code.")
        return value

    def validate(self, data):
        required_fields = ['currency', 'birth_date']
        for field in required_fields:
            if field not in data:
                raise serializers.ValidationError({field: f"{field.title()} is required."})
        return data

    def update(self, instance, validated_data):
        for field in ['currency', 'language', 'theme', 'birth_date', 'receive_email_updates']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance