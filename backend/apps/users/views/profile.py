from typing import Any, cast

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.models import SupportedCountry, SupportedCurrency
from apps.users.serializers import (
    MeSerializer,
    ProfileOptionsSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
)
from apps.users.services import AuthService
from apps.users.views.base import ServiceAPIView


class MeView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = MeSerializer(
            {
                "user": request.user,
                "profile": request.user.profile,
            }
        )
        return Response(serializer.data)


class ProfileView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user.profile)
        return Response(serializer.data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            request.user.profile,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        validated = cast(dict[str, Any], serializer.validated_data)
        profile = AuthService.update_profile(
            user=request.user,
            full_name=validated.get("full_name", request.user.profile.full_name),
            language=validated.get("language", request.user.profile.language),
            timezone_name=validated.get("timezone", request.user.profile.timezone),
            country=validated.get("country", request.user.profile.country),
            currency=validated.get("currency", request.user.profile.currency),
        )

        return Response(ProfileSerializer(profile).data)


class ProfileOptionsView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payload = {
            "countries": list(
                SupportedCountry.objects.filter(is_active=True)
                .order_by("name")
                .values("code", "name")
            ),
            "currencies": list(
                SupportedCurrency.objects.filter(is_active=True)
                .order_by("code")
                .values("code", "name")
            ),
        }
        return Response(ProfileOptionsSerializer(payload).data)
