from djoser.serializers import UserSerializer as BaseUserSerializer, UserCreateSerializer as BaseUserCreateSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Profile
from portfolio.serializers import PortfolioSerializer


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = get_user_model()
        fields = ('id', 'email', 'first_name', 'last_name', 'password')


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = ['id', 'email', 'first_name', 'last_name']

class ProfileSerializer(serializers.ModelSerializer):
    portfolio = PortfolioSerializer(read_only=True)
    email = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['id', 'user', 'email', 'currency', 'language', 'birth_date', 'is_asset_manager', 'portfolio']
        read_only_fields = ['user']

    def get_email(self, obj):
        return obj.user.email