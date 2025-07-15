"""
users.serializers.user
~~~~~~~~~~~~~~~~~~~~~~
Contains basic serializers for representing User model data.
"""

from djoser.serializers import UserSerializer as BaseUserSerializer


class UserSerializer(BaseUserSerializer):
    """
    Basic serializer for User model.
    Used for responses that need minimal user info (id, email, first_name, last_name).
    """
    class Meta(BaseUserSerializer.Meta):
        fields = ['id', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']
