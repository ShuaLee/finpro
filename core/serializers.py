from rest_framework import serializers
from .models import Profile
from portfolio.serializers import PortfolioSerializer


class ProfileSerializer(serializers.ModelSerializer):
    individual_portfolio = PortfolioSerializer(read_only=True)
    email = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['id', 'user', 'email', 'currency', 'language',
                  'birth_date', 'is_asset_manager', 'individual_portfolio']
        read_only_fields = ['user']

    def get_email(self, obj):
        return obj.user.email
