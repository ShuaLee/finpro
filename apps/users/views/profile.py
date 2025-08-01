"""
users.views.profile
~~~~~~~~~~~~~~~~~~~
Handles profile management endpoints for authenticated users.
"""
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.serializers import ProfileSerializer, CompleteProfileSerializer
import logging

logger = logging.getLogger(__name__)


class ProfileView(generics.GenericAPIView):
    """
    Provides endpoints to retrieve and update the user's profile.

    Supported Methods:
    - GET: Retrieve current user's profile
    - PUT: Update full profile
    - PATCH: Partially update profile
    """
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    def put(self, request):
        profile = request.user.profile
        serializer = self.get_serializer(
            profile, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request):
        profile = request.user.profile
        serializer = self.get_serializer(
            profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CompleteProfileView(generics.UpdateAPIView):
    """
    API endpoint to complete user profile after signup.
    Requires: full_name, country, preferred_currency.
    """
    serializer_class = CompleteProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile

    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
