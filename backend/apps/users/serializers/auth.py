from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True, min_length=8, trim_whitespace=False)
    full_name = serializers.CharField(
        required=False, allow_blank=True, max_length=150)
    language = serializers.CharField(
        required=False, allow_blank=True, max_length=16, default="en")
    timezone = serializers.CharField(
        required=False, allow_blank=True, max_length=64, default="UTC")
    currency = serializers.CharField(
        required=False, allow_blank=False, max_length=10, default="USD")
    accept_terms = serializers.BooleanField()

    def validate_email(self, value):
        return value.strip().lower()

    def validate_password(self, value):
        validate_password(value)
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_email(self, value):
        return value.strip().lower()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, allow_blank=True)


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, trim_whitespace=True)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_code(self, value):
        return value.strip()


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(trim_whitespace=True)
    new_password = serializers.CharField(
        write_only=True, min_length=8, trim_whitespace=False)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(
        write_only=True, min_length=8, trim_whitespace=False)

    def validate_new_password(self, value):
        request = self.context.get("request")
        user = request.user if request is not None else None
        validate_password(value, user=user)
        return value


class EmailChangeRequestSerializer(serializers.Serializer):
    new_email = serializers.EmailField()
    current_password = serializers.CharField(
        write_only=True, trim_whitespace=False)

    def validate_new_email(self, value):
        return value.strip().lower()


class EmailChangeConfirmSerializer(serializers.Serializer):
    new_email = serializers.EmailField()
    code = serializers.CharField(max_length=6, trim_whitespace=True)

    def validate_new_email(self, value):
        return value.strip().lower()

    def validate_code(self, value):
        return value.strip()


class TrustedDeviceRevokeSerializer(serializers.Serializer):
    token = serializers.CharField(trim_whitespace=True)
