from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.exceptions import TokenError
from users.serializers import SignupSerializer, LoginSerializer
from users.utils.cookie import set_auth_cookies

User = get_user_model()


class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        response = Response({
            "detail": "Signup successful",
            "user": {"id": user.id, "email": user.email}
        }, status=status.HTTP_201_CREATED)
        return set_auth_cookies(response, refresh.access_token, refresh)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CSRFTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return JsonResponse({"detail": "CSRF cookie set"})


class CookieLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        response = Response({"detail": "Login successful"},
                            status=status.HTTP_200_OK)
        return set_auth_cookies(response, refresh.access_token, refresh)


class CookieLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get refresh token from cookies
        refresh_token = request.COOKIES.get("refresh")

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                # Blacklist the token
                token.blacklist()
            except TokenError:
                pass  # Token already invalid or expired

        # Clear all cookies
        response = Response({"detail": "Logged out"},
                            status=status.HTTP_200_OK)
        response.delete_cookie("access")
        response.delete_cookie("refresh")
        response.delete_cookie("csrftoken")

        return response


class CookieRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token missing"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            token = RefreshToken(refresh_token)
            if BlacklistedToken.objects.filter(token__jti=token["jti"]).exists():
                return Response({"detail": "Token blacklisted"}, status=status.HTTP_401_UNAUTHORIZED)

            if getattr(settings, "SIMPLE_JWT", {}).get("BLACKLIST_AFTER_ROTATION", False):
                token.blacklist()

            user_id = token.get("user_id")
            if not user_id:
                return Response({"detail": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

            user = User.objects.filter(id=user_id).first()
            if not user:
                return Response({"detail": "User not found"}, status=status.HTTP_401_UNAUTHORIZED)

            new_refresh = RefreshToken.for_user(user)
            new_access = new_refresh.access_token
            response = Response({"detail": "Token refreshed"},
                                status=status.HTTP_200_OK)
            return set_auth_cookies(response, new_access, new_refresh)

        except TokenError:
            return Response({"detail": "Invalid or blacklisted token"}, status=status.HTTP_401_UNAUTHORIZED)
