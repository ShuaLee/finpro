from rest_framework import serializers
from .models import IndividualPortfolio


class IndividualPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndividualPortfolio
        fields = ['id', 'profile', 'name', 'created_at']
