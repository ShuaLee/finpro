from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from profiles.serializers import ProfileSerializer, OnboardingCompleteSerializer
from fx.models.country import Country
from fx.models.fx import FXCurrency


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user.profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = ProfileSerializer(
            request.user.profile,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class CompleteOnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = request.user.profile
        serializer = OnboardingCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        if "full_name" in data:
            profile.full_name = data["full_name"]

        if "country" in data:
            profile.country = Country.objects.get(code=data["country"])

        if "currency" in data:
            profile.currency = FXCurrency.objects.get(code=data["currency"])

        profile.onboarding_status = profile.OnboardingStatus.COMPLETED
        profile.onboarding_step = 100
        profile.save()

        return Response(ProfileSerializer(profile).data, status=status.HTTP_200_OK)
