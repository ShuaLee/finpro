from rest_framework import generics
from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from .models import Profile
from .serializers import ProfileSerializer, SignupCompleteSerializer
import requests

class SignupCompleteView(generics.CreateAPIView):
    serializer_class = SignupCompleteSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        # Optional: Auto-login user (requires django-rest-framework-simplejwt)
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        })

class ProfileViewSet(ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def status(self, request):
        profile = self.get_object()
        return Response({'profile_setup_complete': profile.profile_setup_complete})

    @action(detail=False, methods=['get', 'put'])
    def setup(self, request):
        profile = self.get_object()
        if profile.profile_setup_complete and request.method == 'GET':
            return Response({'detail': 'Profile already set up'}, status=400)
        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        if request.method == 'PUT':
            serializer = self.get_serializer(profile, data=request.data, partial=True, context={'is_setup': True})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)