from rest_framework import serializers
from .models import Profile
from portfolio.serializers import IndividualPortfolioSerializer


class ProfileSerializer(serializers.ModelSerializer):
    individual_portfolio = IndividualPortfolioSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'user', 'country', 'individual_portfolio']
        read_only_fields = ['user']
