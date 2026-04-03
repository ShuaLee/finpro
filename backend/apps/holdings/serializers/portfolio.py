from rest_framework import serializers

from apps.holdings.models import Portfolio


class PortfolioSerializer(serializers.ModelSerializer):
    profile_email = serializers.EmailField(source="profile.user.email", read_only=True)

    class Meta:
        model = Portfolio
        fields = [
            "id",
            "profile",
            "profile_email",
            "name",
            "kind",
            "is_default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "profile",
            "profile_email",
            "created_at",
            "updated_at",
        ]


class PortfolioCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    kind = serializers.ChoiceField(
        choices=Portfolio.Kind.choices,
        required=False,
        default=Portfolio.Kind.PERSONAL,
    )
    is_default = serializers.BooleanField(required=False, default=False)

    def validate_name(self, value):
        return value.strip()


class PortfolioUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    kind = serializers.ChoiceField(choices=Portfolio.Kind.choices, required=False)
    is_default = serializers.BooleanField(required=False)

    def validate_name(self, value):
        return value.strip()
