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
            "currency",
        )


class MeSerializer(serializers.Serializer):
    user = UserSerializer(read_only=True)
    profile = ProfileSerializer(read_only=True)
