"""
users.views.profile
~~~~~~~~~~~~~~~~~~~
Handles profile management endpoints for authenticated users.
"""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..serializers import ProfileSerializer
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
        """
        Retrieve the authenticated user's profile.
        """
        profile = request.user.profile
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    def put(self, request):
        """
        Replace the entire profile with provided data.
        """
        profile = request.user.profile
        serializer = self.get_serializer(
            profile, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request):
        """
        Partially update the user's profile.
        """
        profile = request.user.profile
        serializer = self.get_serializer(
            profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
