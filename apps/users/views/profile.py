"""
users.views.profile
~~~~~~~~~~~~~~~~~~~
Handles profile management endpoints for authenticated users.
"""

from rest_framework import status
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import Profile
from users.serializers import ProfileSerializer
from users.services import validate_required_profile_fields
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
        validate_required_profile_fields(
            serializer.validated_data, partial=False)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request):
        profile = request.user.profile
        serializer = self.get_serializer(
            profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validate_required_profile_fields(
            serializer.validated_data, partial=True)
        serializer.save()
        return Response(serializer.data)


class ProfilePlanUpdateView(APIView):
    """
    API endpoint for updating the user's subscription plan.

    Method:
        PATCH /users/profile/plan/

    Request Body Example:
        {
            "plan": "premium"
        }

    Responses:
        200 OK: Profile updated successfully.
        400 Bad Request: Invalid data or plan slug.
        404 Not Found: Profile not found.

    Behavior:
        - Requires authentication.
        - Updates only the subscription plan field.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProfileSerializer(
            profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
