from rest_framework import serializers

from apps.users.models import Profile, User


class UserSerializer(serializers.ModelSerializer):
    is_email_verified = serializers.BooleanField(read_only=True)
    is_locked = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "is_active",
            "is_staff",
            "email_verified_at",
            "is_email_verified",
            "is_locked",
            "date_joined",
        )
        read_only_fields = fields


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = (
            "user",
            "full_name",
            "language",
            "timezone",
            "country",
            "currency",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("user", "created_at", "updated_at")


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            "full_name",
            "language",
            "timezone",
            "country",
            "currency",
        )

    def validate_country(self, value):
        return value.strip().upper()

    def validate_currency(self, value):
        return value.strip().upper()


class ProfileOptionsSerializer(serializers.Serializer):
    countries = serializers.ListField(read_only=True)
    currencies = serializers.ListField(read_only=True)


class MeSerializer(serializers.Serializer):
    user = UserSerializer(read_only=True)
    profile = ProfileSerializer(read_only=True)
