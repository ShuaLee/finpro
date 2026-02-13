from rest_framework import serializers

from profiles.models import Profile
from fx.models.country import Country
from fx.models.fx import FXCurrency
from subscriptions.models import Plan, AccountType


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    country = serializers.SlugRelatedField(
        slug_field="code",
        queryset=Country.objects.all(),
        required=False,
        allow_null=True,
    )
    currency = serializers.SlugRelatedField(
        slug_field="code",
        queryset=FXCurrency.objects.all(),
        required=False,
        allow_null=False,
    )
    plan = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Plan.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    account_type = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=AccountType.objects.all(),
        required=False,
        allow_null=True,
    )

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
            "account_type",
            "receive_email_updates",
            "receive_marketing_emails",
            "onboarding_status",
            "onboarding_step",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "email", "created_at", "updated_at"]


class OnboardingCompleteSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150, required=False, allow_blank=False)
    country = serializers.SlugField(required=False)
    currency = serializers.SlugField(required=False)

    def validate_country(self, value):
        if not Country.objects.filter(code=value.upper()).exists():
            raise serializers.ValidationError("Invalid country code.")
        return value.upper()

    def validate_currency(self, value):
        if not FXCurrency.objects.filter(code=value.upper()).exists():
            raise serializers.ValidationError("Invalid currency code.")
        return value.upper()
