from django.conf import settings
from rest_framework import serializers
from ..models import Profile


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
        valid_codes = [code for code, name in settings.CURRENCY_CHOICES]
        if value not in valid_codes:
            raise serializers.ValidationError(
                f"Invalid currency code. Must be a valid ISO 4217 code (e.g., USD, EUR, AUD).")
        return value

    def update(self, instance, validated_data):
        for field in ['currency', 'language', 'theme', 'receive_email_updates']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance
