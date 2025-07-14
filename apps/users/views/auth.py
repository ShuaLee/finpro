from django.contrib.auth import authenticate
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken
from users.services import bootstrap_user_profile_and_portfolio
from ..serializers import SignupCompleteSerializer
import logging

logger = logging.getLogger(__name__)


class SignupCompleteView(generics.CreateAPIView):
    serializer_class = SignupCompleteSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Initializing Profile and Portfolio
        bootstrap_user_profile_and_portfolio(user)

        # Generate tokens
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
        }, status=status.HTTP_201_CREATED)

@method_decorator(csrf_exempt, name="dispatch")
class CookieLoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)

        response = Response({"detail": "Login successful"},
                            status=status.HTTP_200_OK)
        response.set_cookie(
            key="access",
            value=str(refresh.access_token),
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=60 * 5  # 5 minutes
        )
        response.set_cookie(
            key="refresh",
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=60 * 60 * 24 * 7  # 7 days
        )
        return response


@method_decorator(csrf_exempt, name="dispatch")
class CookieLogoutView(APIView):
    def post(self, request):
        response = Response({"detail": "Logged out"},
                            status=status.HTTP_200_OK)
        response.delete_cookie("access")
        response.delete_cookie("refresh")
        return response


class CookieRefreshView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh")
        if not refresh_token:
            return Response({"detail": "No refresh token"}, status=401)

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
        except InvalidToken:
            return Response({"detail": "Invalid refresh"}, status=401)

        res = Response({"detail": "Token refreshed"})
        res.set_cookie(
            "access",
            access_token,
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=60 * 5,
        )
        return res
