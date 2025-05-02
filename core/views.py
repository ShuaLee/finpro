from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from .serializers import ProfileSerializer


class ProfileViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Ignore any pk in the URL and return the authenticated user's profile
        return self.request.user.profile

    def retrieve(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(
            profile, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
