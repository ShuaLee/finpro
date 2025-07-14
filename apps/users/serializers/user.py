from djoser.serializers import UserSerializer as BaseUserSerializer



class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = ['id', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']
