from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProfileSerializer
from .models import Profile

# Create your views here.


class ProfileViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        profile = request.user.profile
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        profile = request.user.profile
        serializer = self.get_serializer(
            profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
