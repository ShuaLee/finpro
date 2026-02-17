from zoneinfo import available_timezones

from rest_framework import serializers

from fx.models.country import Country
from fx.models.fx import FXCurrency
from profiles.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    country = serializers.SlugRelatedField(
        slug_field="code",
        queryset=Country.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    currency = serializers.SlugRelatedField(
        slug_field="code",
        queryset=FXCurrency.objects.filter(is_active=True),
        required=False,
        allow_null=False,
    )

    # Never user-editable directly from profile patch endpoint.
    plan = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "email",
            "full_name",
            "birth_date",
            "language",
            "timezone",
            "country",
            "currency",
            "plan",
            "receive_email_updates",
            "receive_marketing_emails",
            "onboarding_status",
            "onboarding_step",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "plan",
            "onboarding_status",
            "onboarding_step",
            "created_at",
            "updated_at",
        ]

    def validate_language(self, value):
        normalized = (value or "").strip().lower()
        if len(normalized) < 2 or len(normalized) > 16:
            raise serializers.ValidationError("Language must be between 2 and 16 chars.")
        return normalized

    def validate_timezone(self, value):
        tz = (value or "").strip()
        if tz not in available_timezones():
            raise serializers.ValidationError("Invalid timezone.")
        return tz


class OnboardingCompleteSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150, required=False, allow_blank=False)
    country = serializers.SlugField(required=False)
    currency = serializers.SlugField(required=False)

    def validate_country(self, value):
        if not Country.objects.filter(code=value.upper(), is_active=True).exists():
            raise serializers.ValidationError("Invalid country code.")
        return value.upper()

    def validate_currency(self, value):
        if not FXCurrency.objects.filter(code=value.upper(), is_active=True).exists():
            raise serializers.ValidationError("Invalid currency code.")
        return value.upper()
