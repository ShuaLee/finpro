from datetime import date
from djoser.serializers import UserSerializer as BaseUserSerializer, UserCreateSerializer as BaseUserCreateSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from core.constants import CURRENCY_CHOICES
from .models import Profile



class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = get_user_model()
        fields = ('id', 'email', 'first_name', 'last_name', 'birth_date', 'password')

class SignupCompleteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    birth_date = serializers.DateField(required=True)

    def validate_birth_date(self, value):
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 13:
            raise serializers.ValidationError("User must be at least 13 years old.")
        return value

    def validate_email(self, value):
        if get_user_model().objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_password(self, value):
        # Use Django's password validation
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
        profile.language = self.context.get('request').META.get('HTTP_ACCEPT_LANGUAGE', 'en').split(',')[0].split('-')[0].lower() or 'en'
        profile.profile_setup_complete = True
        profile.save()

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
            'email', 'currency', 'language',
            'created_at', 'receive_email_updates', 
            'theme'
        ]
        read_only_fields = ['created_at', 'email']

    def get_email(self, obj):
        return obj.user.email

    def validate_currency(self, value):
        valid_codes = [code for code, name in CURRENCY_CHOICES]
        if value not in valid_codes:
            raise serializers.ValidationError(f"Invalid currency code. Must be a valid ISO 4217 code (e.g., USD, EUR, AUD).")
        return value

    def update(self, instance, validated_data):
        for field in ['currency', 'language', 'theme', 'receive_email_updates']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance