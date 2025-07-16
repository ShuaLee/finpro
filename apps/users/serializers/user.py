"""
users.serializers.user
~~~~~~~~~~~~~~~~~~~~~~
Contains basic serializers for representing User model data.
"""

from djoser.serializers import UserSerializer as BaseUserSerializer


class UserSerializer(BaseUserSerializer):
    """
    Basic serializer for User model.
    Used for responses that need minimal user info (id, email).
    """
    class Meta(BaseUserSerializer.Meta):
        fields = ['id', 'email']
        read_only_fields = ['id', 'email']
